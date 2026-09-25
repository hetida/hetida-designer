"""Documentation for Hetida Platform Signal Timeseries Data

# Hetida Platform Signal Timeseries Data

## Description
This component is meant to be used via the [component adapter](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/component_adapter.md) via [URI Wirings](https://github.com/hetida/hetida-designer/blob/release/docs/execution/uri_wirings.md) in [hetida platform](https://hetida.io/). It enables fetching timeseries data of dynamically resolved collections of multiple hetida platform signals into a MULTITSFRAME.

As an example, you might want to load all timeseries data of those signals under a certain asset in your hierarchy, that represent an energy consumption measurement, e.g. in order to sum them up.

Note that typically a URI Wiring shortcut `hd://timeseries` points to the newest revision of this component.

## Inputs
* **asset_node_id** (str, optional, default value `None`): Asset node id. If None, will be inferred from execution context which the hetida platform provides: The parent asset of the currently executed virtual signal or workflow configuration. If not provided either way, a ValueError will be raised.
* **timestampFrom** (str): Isoformat timestamp or [dtexp](https://github.com/stewit/dtexp) expression defining start of interval to load. hetida platform will provide this automatically, but it can be overriden through an explicit value.
* **timestampTo** (str):  Isoformat timestamp or [dtexp](https://github.com/stewit/dtexp) expression defining end of interval to load. hetida platform will provide this automatically, but it can be overriden through an explicit value.
* **recursive** (bool, optional, default value True): If True signals are collected recursively. If False, only signals directly under the asset of `asset_node_id` are considered.
* **starts_with** (str, optional, default value None): If set, restrict to signals with name starting with this string. Case-insensitive.
* **name_regexp** (str, optional, default value None). If not None, only signals whose name match the provided regexp will be considered.
* **relative_name_path_regexp** (str, optional, default value None). If not None, only signals whose explorer "relative name path" match the provided regexp will be considered.
* **measurement** (ANY, expects str or list of strings, optional, default value `None`): Either a single string or an array of strings or null. If not null, only signals having one of the provided measurements are collected.
* **include_ingestion_signals** (bool, optional, default value True): Whether ingestion signals should be included
* **include_virtual_signals** (bool, optional, default value True): Whether virtual signals should be included. Transient virtual signals are never included, see Details.
* **use_as_metric** (str, optional, default value "externalTimeSeriesId"): Which field of the signal is used to identify its metric. In the resulting multitsframe this will define what is used in the metric column. Make sure to select a field with unique value per metric (e.g. "id", which always is the signal id). Note that the values "externalTimeSeriesId" or "relativeNamePath", while being more verbose, do not necessarily have to be unique. The component aborts with a ValueError if the selected field does not uniquely identify the actually loaded metrics.

## Outputs

* **ts_data** (Multitsframe): Contains the loaded timeseries data.

## Details

For trafos employed via the hetida platform at a specific point in its asset hierarchy, e.g. in virtual signals or workflow configurations, it automatically infers the current asset node id from the invocation context and collects data from there. In hetida platform you typically employ it using an URI wiring in such a configuration.

Requires the env variable `HETIDA_PLATFORM_API_URL` to be set for the designer runtime to point to the hetida platform core api, e.g. "http://test-hetida-platform-core-backend-svc:8080/api" in a K8S setup or "http://core-backend:8080/api" in a docker-compose setup. Requests to it use the timeout (`EXTERNAL_REQUEST_TIMEOUT`, in seconds) and certificate verification setting (`HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS`) configured for the runtime's requests to adapters.

Since it uses the hetida platform hetida designer adapter REST service to fetch data it requires the runtime to know its adapter key and expects this adapter [to be configured](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/adapter_registration.md) for the runtime service. If the adapter key differs from `hetida-platform-adapter` it must be configured for the runtime using the `HETIDA_PLATFORM_ADAPTER_KEY` environment variable.

Transient virtual signals are always excluded: They have no stored timeseries and hetida platform does not execute them when their data is requested via the hetida designer adapter. Instead it rejects the complete data request. Skipped transient signals are logged.

Requires a hetida platform version whose node children endpoint provides `id`, `measurement` and `externalTimeSeriesId` in the `referenceObject` of signal nodes. With older versions the `measurement` filter and the default `use_as_metric` value "externalTimeSeriesId" fail with an error pointing this out. Choose e.g. "relativeNamePath" or "id" as `use_as_metric` then.

Metadata will be present in the resulting DataFrame's attrs attribute, following hetida designer [metadata conventions](https://github.com/hetida/hetida-designer/blob/release/docs/metadata_attrs.md).

You may also use this component as a good starting point to write your own variant for dynamical selection of signal timeseries data which fits your specific hetida platform setup and use cases.

## Examples

E.g. the URI wiring
```
hd://component-adapter/<ID_OF_THIS_COMPONENT>?measurement=energyconsumption&include_virtual_signals=false
```
or
```
hd://timeseries?measurement=energyconsumption&include_virtual_signals=false
```

will load all ingestion signals (but not virtual signals) that have "energyconsumption" configured as measurement.
"""

import logging
import os
import re
from collections import defaultdict
from copy import deepcopy
from posixpath import join as posix_urljoin
from uuid import UUID

import httpx
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from hdutils import ComponentInputValidationException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_ts_data import load_ts_data_from_adapter
from hetdesrun.dt_utils import resolve_interval
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.runtime.context import (
    get_hierarchy_object_info,
)
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


HETIDA_PLATFORM_ADAPTER_KEY = os.environ.get(
    "HETIDA_PLATFORM_ADAPTER_KEY", "hetida-platform-adapter"
)
EXPLORER_SEP_CHAR = "/"

# Maximum length of response text included in error messages
MAX_ERROR_TEXT_LENGTH = 1000


def get_platform_api_url() -> str:
    """Obtain the hetida platform core api url from the environment

    Read at execution time, so that the component can be imported on designer instances
    without hetida platform. Raises ValueError if not set or invalid.
    """
    platform_api_url = os.environ.get("HETIDA_PLATFORM_API_URL", "").strip()
    if not platform_api_url.startswith(("http://", "https://")):
        raise ValueError(
            "Environment variable HETIDA_PLATFORM_API_URL is "
            + (f"invalid ({platform_api_url!r})" if platform_api_url else "not set")
            + " for the hetida designer runtime. It must point to the hetida platform core api,"
            ' e.g. "http://core-backend:8080/api" (docker compose) or'
            ' "http://test-hetida-platform-core-backend-svc:8080/api" (K8S).'
        )
    return platform_api_url


async def get_external_auth_headers():
    return await get_auth_headers(external=True)


class HetidaPlatformRequestError(Exception):
    """A request to the hetida platform core api failed"""


def platform_error_reason(resp: httpx.Response) -> str:
    """Extract the reason from a hetida platform error response

    hetida platform error responses carry the reason in the "message" field of a json body.
    Otherwise (e.g. html error pages of proxies) the beginning of the response text is used.
    """
    try:
        message = resp.json().get("message")
    except ValueError, AttributeError:
        message = None
    if isinstance(message, str) and message.strip() != "":
        return message

    text = resp.text.strip()
    if text == "":
        return "(empty response body)"
    if len(text) > MAX_ERROR_TEXT_LENGTH:
        return text[:MAX_ERROR_TEXT_LENGTH] + "..."
    return text


async def fetch_node_children(platform_api_url: str, asset_node_id: str, params: dict) -> list:
    """Obtain the children of a node from the hetida platform node children endpoint

    Raises HetidaPlatformRequestError if the platform cannot be reached or the request fails.
    """
    children_url = posix_urljoin(platform_api_url, "nodes", asset_node_id, "children")
    request_description = f"GET {children_url}"
    headers = await get_external_auth_headers()

    try:
        async with httpx.AsyncClient(
            timeout=get_config().external_request_timeout,
            verify=get_config().hd_adapters_verify_certs,
        ) as client:
            resp = await client.get(children_url, headers=headers, params=params)
    except httpx.TimeoutException as e:
        msg = (
            f"hetida platform core api did not answer in time ({request_description}):"
            f" {type(e).__name__}. The timeout of {get_config().external_request_timeout} s"
            " can be configured for the runtime via EXTERNAL_REQUEST_TIMEOUT."
        )
        logger.error(msg)
        raise HetidaPlatformRequestError(msg) from e
    except httpx.RequestError as e:
        msg = (
            f"Could not reach hetida platform core api at {platform_api_url}"
            f" ({request_description}): {type(e).__name__}: {e}"
        )
        logger.error(msg)
        raise HetidaPlatformRequestError(msg) from e

    if resp.status_code != 200:
        msg = (
            f"Request to hetida platform ({request_description}) failed with status"
            f" {resp.status_code}: {platform_error_reason(resp)}"
        )
        logger.error(msg)
        raise HetidaPlatformRequestError(msg)

    try:
        return resp.json()
    except ValueError as e:
        msg = f"Request to hetida platform ({request_description}) returned invalid json: {e}"
        logger.error(msg)
        raise HetidaPlatformRequestError(msg) from e


class HetidaPlatformResponseError(Exception):
    """A hetida platform response does not match what this component expects"""


class PlatformNode(BaseModel):
    """A node (NodeDto) of the hetida platform node children endpoint

    Only contains the fields this component relies on. Validation only checks the response,
    the component continues working with the unchanged response data (extra="allow").
    """

    model_config = ConfigDict(extra="allow")

    id: str
    nodeType: str
    name: str | None = None
    parentIdPath: str | None = None


def describe_node(node, index: int) -> str:
    if isinstance(node, dict):
        if node.get("name") is not None:
            return f"'{node['name']}' (id {node.get('id')})"
        if node.get("id") is not None:
            return f"with id {node['id']}"
    return f"at index {index}"


def format_validation_error(e: ValidationError) -> str:
    return "; ".join(
        (".".join(str(part) for part in error["loc"]) or "node") + ": " + error["msg"]
        for error in e.errors(include_url=False)
    )


def validate_nodes(nodes: list, model: type[BaseModel], node_kind: str) -> None:
    """Validate nodes of the node children response against a model

    Raises HetidaPlatformResponseError naming the first invalid node.
    """
    for index, node in enumerate(nodes):
        try:
            model.model_validate(node)
        except ValidationError as e:
            raise HetidaPlatformResponseError(
                "hetida platform node children response does not match what this component"
                f" expects: {node_kind} {describe_node(node, index)}: {format_validation_error(e)}"
            ) from e


def validate_node_children(response) -> list:
    """Validate the node children response, returning it unchanged"""
    if not isinstance(response, list):
        raise HetidaPlatformResponseError(
            "hetida platform node children response does not match what this component"
            f" expects: Expected a list of nodes, got {type(response).__name__}."
        )
    validate_nodes(response, PlatformNode, "node")
    return response


class SignalReference(BaseModel):
    """referenceObject of signal nodes: the fields this component relies on

    measurement and externalTimeSeriesId are only checked where they are actually needed (see
    ensure_signal_reference_field), since older hetida platform versions do not provide them.
    """

    model_config = ConfigDict(extra="allow")

    isTransient: bool = False


class SignalNode(PlatformNode):
    name: str
    referenceId: str
    parentIdPath: str = Field(min_length=1)
    referenceObject: SignalReference


# referenceObject fields of signal nodes, which older hetida platform versions do not provide
SIGNAL_REFERENCE_PLATFORM_FIELDS = ("measurement", "externalTimeSeriesId")


def ensure_signal_reference_field(signal_children, field: str, purpose: str) -> None:
    """Raise HetidaPlatformResponseError if field is missing in the referenceObject of signals"""
    missing = [child for child in signal_children if field not in child["referenceObject"]]
    if len(missing) > 0:
        raise HetidaPlatformResponseError(
            "The referenceObject of the signal nodes "
            + ", ".join(f"'{child['name']}' (id {child['id']})" for child in missing[:5])
            + (f" and {len(missing) - 5} more" if len(missing) > 5 else "")
            + f" has no '{field}', which is required {purpose}. The hetida platform version is"
            " probably too old: Its node children endpoint must provide id, measurement and"
            " externalTimeSeriesId in the referenceObject of signal nodes."
        )


def validate_measurement(measurement) -> set[str] | None:
    """Validate the measurement input, returning the allowed measurements or None"""
    if isinstance(measurement, str):
        return {measurement}
    try:
        validated = TypeAdapter(list[str] | None).validate_python(measurement)
    except ValidationError as e:
        raise ComponentInputValidationException(
            "measurement must be a measurement name or a list of measurement names,"
            f" got {measurement!r}.",
            invalid_component_inputs=["measurement"],
        ) from e
    return None if validated is None else set(validated)


def ensure_asset_node_id(asset_node_id: str | None) -> str:
    """Ensure asset node id is present, trying to load from context if not provided explicitely

    Returns the id in normalized form (lower case uuid string), since it is compared with
    ids from hetida platform responses.

    Raises ValueError if id is neither provided directly nor available in context or if the id
    from context is not a valid UUID. Raises ComponentInputValidationException if the directly
    provided id is not a valid UUID.
    """
    if asset_node_id is None:
        hierarchy_object = get_hierarchy_object_info()

        logger.debug("Loaded hierarchy object: %s", str(hierarchy_object))

        # Do we need other attributes: id, node_id, parent_node_id, type?
        if hierarchy_object.parent_node_id is None:
            raise ValueError("No asset id provided: Neither directly nor by context.")

        try:
            asset_node_id = str(UUID(str(hierarchy_object.parent_node_id).strip()))
        except ValueError as e:
            raise ValueError(
                f"The asset node id {hierarchy_object.parent_node_id!r} provided by context"
                " is not a valid UUID."
            ) from e
        logger.debug(
            "Using asset node id from hierarchy_object provided via context: %s",
            asset_node_id,
        )
    else:
        try:
            asset_node_id = str(UUID(str(asset_node_id).strip()))
        except ValueError as e:
            raise ComponentInputValidationException(
                f"The provided asset_node_id {asset_node_id!r} is not a valid UUID.",
                invalid_component_inputs=["asset_node_id"],
            ) from e
        logger.debug("Using asset_node_id provided directly from input: %s", asset_node_id)
    return asset_node_id


def exclude_transient_signals(signal_children):
    """Remove transient virtual signals, logging the skipped ones

    Transient virtual signals have no stored timeseries and hetida platform rejects data
    requests including them via the hetida designer adapter.
    """
    transient_children = [
        child
        for child in signal_children
        if (child.get("referenceObject") or {}).get("isTransient", False)
    ]
    if len(transient_children) > 0:
        logger.info(
            "Skipping transient virtual signals, since they have no stored timeseries: %s",
            ", ".join(f"'{child['name']}' (id {child['id']})" for child in transient_children),
        )

    return [child for child in signal_children if child not in transient_children]


def metric_metadata_from_child(child, attrs_from_adapter, metric_key, metric_value):
    """Built metric metadata from hierarchy object

    metric_value is the value used for this signal in the metric column. It is set
    under metric_key, so that metadata can be matched to the data via
    dataset_metadata.metric_key, even if the value does not stem from the referenceObject.
    """

    metric_object = deepcopy(child["referenceObject"])
    metric_object.pop("schedulerJob", None)
    metric_object.pop("outputDefinitions", None)
    metric_object["hierarchy_object"] = child

    metric_object["relativeNamePath"] = child["relativeNamePath"]
    metric_object[metric_key] = metric_value

    try:  # noqa: SIM105
        metric_object["inherited"] = attrs_from_adapter[child["referenceId"]][
            "single_metric_metadata"
        ]["structured_metadata"]["inherited"]
    except KeyError:
        pass
    try:  # noqa: SIM105
        metric_object["comments"] = attrs_from_adapter[child["referenceId"]][
            "single_metric_metadata"
        ]["structured_metadata"]["comments"]
    except KeyError:
        pass

    return metric_object


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "asset_node_id": {"data_type": "STRING", "default_value": None},
        "timestampFrom": {"data_type": "STRING"},
        "timestampTo": {"data_type": "STRING"},
        "starts_with": {"data_type": "STRING", "default_value": None},
        "recursive": {"data_type": "BOOLEAN", "default_value": True},
        "name_regexp": {"data_type": "STRING", "default_value": None},
        "relative_name_path_regexp": {"data_type": "STRING", "default_value": None},
        "measurement": {"data_type": "ANY", "default_value": None},
        "include_ingestion_signals": {"data_type": "BOOLEAN", "default_value": True},
        "include_virtual_signals": {"data_type": "BOOLEAN", "default_value": True},
        "use_as_metric": {
            "data_type": "STRING",
            "default_value": "externalTimeSeriesId",
        },
    },
    "outputs": {
        "ts_data": {"data_type": "MULTITSFRAME"},
    },
    "name": "Hetida Platform Signal Timeseries Data",
    "category": "hetida platform Sources",
    "description": "Load multiple signal timeseries data from hetida platform",
    "version_tag": "0.1.11",
    "id": "0adf6cff-b7ea-4fb5-aea9-43c41cafe415",
    "revision_group_id": "c8c22f6a-b046-4c50-9364-5cbb517cfb97",
    "state": "RELEASED",
    "released_timestamp": "2026-09-24T20:38:39.408266+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


async def main(
    *,
    timestampFrom,
    timestampTo,
    asset_node_id=None,
    starts_with=None,
    recursive=True,
    name_regexp=None,
    relative_name_path_regexp=None,
    measurement=parse_default_value(COMPONENT_INFO, "measurement"),
    include_ingestion_signals=True,
    include_virtual_signals=True,
    use_as_metric="externalTimeSeriesId",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    platform_api_url = get_platform_api_url()

    asset_node_id = ensure_asset_node_id(asset_node_id)

    allowed_measurements = validate_measurement(measurement)

    start, end = resolve_interval(timestampFrom, timestampTo)

    # Obtain and filter children
    all_children = validate_node_children(
        await fetch_node_children(platform_api_url, asset_node_id, params={"recursive": recursive})
    )

    signal_children = [
        child
        for child in all_children
        if (
            child["nodeType"] == "SIGNAL"
            and (include_ingestion_signals or (include_ingestion_signals is None))
        )
        or (
            child["nodeType"] == "VIRTUAL_SIGNAL"
            and (include_virtual_signals or (include_virtual_signals is None))
        )
    ]

    validate_nodes(signal_children, SignalNode, "signal node")

    selected_children = exclude_transient_signals(signal_children)

    id_name_dict = {child["id"]: child.get("name") for child in all_children}
    for child in selected_children:
        id_path_parts_from_root = child["parentIdPath"].split("_")[::-1]
        asset_node_id_index = id_path_parts_from_root.index(asset_node_id)
        child["relativeNamePath"] = EXPLORER_SEP_CHAR.join(
            [
                id_name_dict.get(part) or "NO NAME AVAILABLE"
                for part in id_path_parts_from_root[asset_node_id_index + 1 :]
            ]
            + [child["name"]]
        )

    # Filter by name prefix (case insensitive)
    selected_children = [
        child
        for child in selected_children
        if child["name"].lower().startswith(starts_with.lower() if starts_with else "")
    ]

    # Filter by name_regexp
    if name_regexp:
        selected_children = [
            child
            for child in selected_children
            if (re.fullmatch(name_regexp, child["name"]) is not None)
        ]

    # Filter by relative_name_path_regexp
    if relative_name_path_regexp:
        selected_children = [
            child
            for child in selected_children
            if (re.fullmatch(relative_name_path_regexp, child["relativeNamePath"]) is not None)
        ]

    # Filter by measurement
    if allowed_measurements is not None:
        ensure_signal_reference_field(
            selected_children, "measurement", "for filtering by measurement"
        )
        selected_children = [
            child
            for child in selected_children
            if (child_measurement := child["referenceObject"].get("measurement")) is not None
            and child_measurement in allowed_measurements
        ]

    # Determine the values for the metric column (by signal id) and check them before
    # loading any data
    if use_as_metric in SIGNAL_REFERENCE_PLATFORM_FIELDS:
        ensure_signal_reference_field(selected_children, use_as_metric, "as use_as_metric")
    metric_mapping_dict = {
        child["referenceId"]: (
            # "id" is always the signal id (not the node id), independent of the referenceObject
            child["referenceId"]
            if use_as_metric == "id"
            else child["referenceObject"].get(use_as_metric, child.get(use_as_metric))
        )
        for child in selected_children
    }

    missing_metric_values = [
        f"'{child['name']}' (id {child['referenceId']})"
        for child in selected_children
        if (value := metric_mapping_dict[child["referenceId"]]) is None
        or (isinstance(value, str) and value.strip() == "")
    ]
    if len(missing_metric_values) > 0:
        raise ValueError(
            f"The selected {use_as_metric=} has no value for the signals "
            + ", ".join(missing_metric_values)
            + ". Choose another field for use_as_metric, e.g. 'id' or 'relativeNamePath'."
        )

    value_to_keys = defaultdict(list)
    for key, value in metric_mapping_dict.items():
        value_to_keys[value].append(key)
    duplicates = {val: keys for val, keys in value_to_keys.items() if len(keys) > 1}
    if len(duplicates) > 0:
        raise ValueError(
            f"The selected {use_as_metric=} has {duplicates=} for the loaded metrics. Aborting."
        )

    if len(selected_children) == 0:
        logger.info("No children selected at all for loading signal data.")
        loaded_ts_data = pd.DataFrame()

    else:
        # Load data from adapter timeseries endpoint
        loaded_ts_data = await load_ts_data_from_adapter(
            filtered_sources=[
                FilteredSource(
                    ref_id=child["referenceId"],  # signal id => will become timeseriesId column
                    ref_id_type="SOURCE",
                    filters={"timestampFrom": start, "timestampTo": end},
                    type=ExternalType.TIMESERIES_NUMERIC,
                )
                for child in selected_children
            ],
            filter_params=[("from", start.isoformat()), ("to", end.isoformat())],
            adapter_key=HETIDA_PLATFORM_ADAPTER_KEY,
        )

    if len(loaded_ts_data) == 0:
        attrs = loaded_ts_data.attrs
        loaded_ts_data = pd.DataFrame(columns=["timestamp", "timeseriesId", "value"])
        loaded_ts_data.attrs = attrs

    # metric column
    loaded_ts_data.rename(
        columns={"timeseriesId": "metric"},
        inplace=True,  # noqa:PD002
    )

    # At this point, the signal id (referenceId of the node) is used in the data in metric column
    # Now we transform the data to use the field specified by use_as_metric instead!
    loaded_ts_data["metric"] = loaded_ts_data["metric"].map(metric_mapping_dict)

    # Set metadata accordingly

    attrs_from_adapter = loaded_ts_data.attrs

    loaded_ts_data.attrs = {
        "dataset_metadata": {
            "metric_key": use_as_metric,
            "queried_metrics": [
                metric_mapping_dict[child["referenceId"]] for child in selected_children
            ],
            "ref_interval_start_timestamp": start.isoformat(),
            "ref_interval_end_timestamp": end.isoformat(),
            "ref_interval_type": "closed",
        },
        "metrics": [
            metric_metadata_from_child(
                child,
                attrs_from_adapter,
                metric_key=use_as_metric,
                metric_value=metric_mapping_dict[child["referenceId"]],
            )
            for child in selected_children
        ],
    }

    # log loaded data per timeseries

    loaded_data_points_per_metric = {
        metric_mapping_dict[signal_id := child["referenceId"]]: len(
            loaded_ts_data[loaded_ts_data.metric == metric_mapping_dict[signal_id]]
        )
        for child in selected_children
    }

    logger.info(
        "Loaded data points per metric: %s",
        loaded_data_points_per_metric,
        extra={"loaded_data_points_per_metric": loaded_data_points_per_metric},
    )

    return {"ts_data": loaded_ts_data}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "asset_node_id",
            "filters": {"value": "646e2593-996c-4f60-b591-bceed1e4010b"},
        },
        {
            "workflow_input_name": "timestampFrom",
            "filters": {"value": "2026-02-04T10:00:00+00:00"},
        },
        {
            "workflow_input_name": "timestampTo",
            "filters": {"value": "2026-02-06T10:00:00+00:00"},
        },
        {
            "workflow_input_name": "starts_with",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "recursive",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "name_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "relative_name_path_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "measurement",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "include_ingestion_signals",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "include_virtual_signals",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "use_as_metric",
            "filters": {"value": "relativeNamePath"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "asset_node_id",
            "filters": {"value": "646e2593-996c-4f60-b591-bceed1e4010b"},
        },
        {
            "workflow_input_name": "timestampFrom",
            "filters": {"value": "2026-02-04T10:00:00+00:00"},
        },
        {
            "workflow_input_name": "timestampTo",
            "filters": {"value": "2026-02-06T10:00:00+00:00"},
        },
        {
            "workflow_input_name": "starts_with",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "recursive",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "name_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "relative_name_path_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "measurement",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "include_ingestion_signals",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "include_virtual_signals",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "use_as_metric",
            "filters": {"value": "relativeNamePath"},
        },
    ]
}


# %%
