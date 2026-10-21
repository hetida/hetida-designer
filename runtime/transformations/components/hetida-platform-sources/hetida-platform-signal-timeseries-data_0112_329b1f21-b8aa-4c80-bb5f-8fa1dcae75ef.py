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
* **property_label** (str, optional, default value `None`), **property_condition** (str, optional, default value "equals"), **property_value** (ANY, optional, default value `None`): A single property filter, see "Property filters" in the Details. Only used if `property_label` is set.
* **property_filters** (ANY, optional, default value `None`): A list (json array) of property filters, each an object with keys "label", "condition" (optional, default "equals") and "value", see "Property filters" in the Details. All property filters (including the one given via `property_label`) must apply.
* **include_ingestion_signals** (bool, optional, default value True): Whether ingestion signals should be included
* **include_virtual_signals** (bool, optional, default value True): Whether virtual signals should be included. Transient virtual signals are never included, see Details.
* **use_as_metric** (str, optional, default value "external_id"): Which field of the signal is used to identify its metric. In the resulting multitsframe this will define what is used in the metric column. "external_id" is the name of the signal's timeseries in hetida platform, which the hierarchy calls "externalTimeSeriesId". Make sure to select a field with unique value per metric (e.g. "id", which always is the signal id). Note that the values "external_id" or "relativeNamePath", while being more verbose, do not necessarily have to be unique, e.g. several signals may share a timeseries. The component aborts with a ValueError if the selected field does not uniquely identify the actually loaded metrics.

## Outputs

* **ts_data** (Multitsframe): Contains the loaded timeseries data.

## Details

For trafos employed via the hetida platform at a specific point in its asset hierarchy, e.g. in virtual signals or workflow configurations, it automatically infers the current asset node id from the invocation context and collects data from there. In hetida platform you typically employ it using an URI wiring in such a configuration.

Requires the env variable `HETIDA_PLATFORM_API_URL` to be set for the designer runtime to point to the hetida platform core api, e.g. "http://test-hetida-platform-core-backend-svc:8080/api" in a K8S setup or "http://core-backend:8080/api" in a docker-compose setup. Requests to it use the timeout (`EXTERNAL_REQUEST_TIMEOUT`, in seconds) and certificate verification setting (`HETIDA_DESIGNER_ADAPTERS_VERIFY_CERTS`) configured for the runtime's requests to adapters.

Since it uses the hetida platform hetida designer adapter REST service to fetch data it requires the runtime to know its adapter key and expects this adapter [to be configured](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/adapter_registration.md) for the runtime service. If the adapter key differs from `hetida-platform-adapter` it must be configured for the runtime using the `HETIDA_PLATFORM_ADAPTER_KEY` environment variable.

Transient virtual signals are always excluded: They have no stored timeseries and hetida platform does not execute them when their data is requested via the hetida designer adapter. Instead it rejects the complete data request. Skipped transient signals are logged.

Requires a hetida platform version whose node children endpoint provides `id`, `measurement` and `externalTimeSeriesId` in the `referenceObject` of signal nodes. With older versions the `measurement` filter and the `use_as_metric` values "external_id" (the default) and "externalTimeSeriesId" fail with an error pointing this out. Choose e.g. "relativeNamePath" or "id" as `use_as_metric` then.

### Property filters

A property filter restricts to signals whose property with the given label satisfies a condition. The effective property value of a signal is used: Its own value, or if it does not have one, the value it inherits from the nearest ancestor in the hierarchy having a value. In hetida platform a property without value (null or empty string) means "inherit". Inherited values require a hetida platform version providing inherited properties on the node children endpoint (`withInheritedProperties` query parameter), older versions only provide the signals' own values. Signals without an effective value for the property never match.

The possible conditions are:
* "equals": The property value equals the given value (a string, number or boolean). The comparison respects the property type: FLOAT, INTEGER and BOOLEAN properties are compared as numbers or booleans (e.g. "42" equals 42 and "true" equals true), DATE properties as points in time and all others as strings.
* "any" and "all": The given value is a comma-separated string or a list of strings. The property value is interpreted as comma-separated list, too. "any" requires at least one of the given items to occur in the property value, "all" requires all of them to occur. Items are compared as strings, ignoring surrounding whitespace, case-sensitive.
* "exists": The signal has an effective value for the property. A given value is ignored.

Invalid property filters (e.g. an unknown condition or a missing value) abort the execution before any data is loaded.

### Metadata

Metadata will be present in the resulting DataFrame's attrs attribute, following hetida designer [metadata conventions](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/): `dataset_metadata` contains the queried interval, the queried metrics and the `use_as_metric` field as `metric_key`. Under `metrics` there is an entry for each selected signal: the metadata which the hetida platform provides for the signal when loading its data, e.g. `name`, `description`, `external_id`, the inherited properties under `inherited`, the comments in the queried interval under `comments`, unit, measurement and value data type of its value dimension under `value_dimensions` and its `default_aggregation_method`. Additionally it contains the `use_as_metric` field with the value used in the metric column, if the hetida platform does not provide this field itself (e.g. "relativeNamePath" or "externalTimeSeriesId").

This requires a hetida platform version which provides its metadata following the metadata conventions (hetida platform 2603.1012 or newer). Otherwise the component fails with an error pointing this out.

The component checks the metadata of each loaded signal against the metadata conventions for a SERIES. If it does not adhere to them, e.g. because a value dimension lacks its unit, the component logs a warning naming the signal and listing the found issues, but nevertheless returns the data. The check is skipped if the runtime validates the metadata received from the hetida platform adapter itself ("WARN" or "ERROR" configured for it via `GENERIC_REST_ADAPTER_METADATA_VALIDATION`, see [Validating received metadata](https://hetida.github.io/hetida-designer/integration_guide/adapter_system/adapter_registration/#validating-received-metadata)), since then the runtime logs the issues or lets loading fail.

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

The URI wiring
```
hd://timeseries?property_label=usage&property_condition=any&property_value=heating,cooling
```

will load all signals whose (possibly inherited) property "usage" contains "heating" or "cooling" in its comma-separated value.
"""

import logging
import os
import re
from collections import defaultdict
from copy import deepcopy
from posixpath import join as posix_urljoin
from typing import Any, Literal, Self
from uuid import UUID

import httpx
import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    model_validator,
)

from hdutils import ComponentInputValidationException
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_ts_data import load_ts_data_from_adapter
from hetdesrun.dt_utils import resolve_interval
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.models.metadata_conventions import check_metadata_conventions
from hetdesrun.runtime.context import (
    get_hierarchy_object_info,
)
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import MetadataValidationMode, get_config

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


def format_validation_error(e: ValidationError, root_name: str = "node") -> str:
    return "; ".join(
        (".".join(str(part) for part in error["loc"]) or root_name) + ": " + error["msg"]
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


class PlatformProperty(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str | None = None
    type: str | None = None
    value: Any = None


class InheritedPlatformProperty(PlatformProperty):
    inheritedFromNodeId: str | None = None
    inheritedFromName: str | None = None


class SignalReference(BaseModel):
    """referenceObject of signal nodes: the fields this component relies on

    measurement and externalTimeSeriesId are only checked where they are actually needed (see
    ensure_signal_reference_field), since older hetida platform versions do not provide them.
    """

    model_config = ConfigDict(extra="allow")

    isTransient: bool = False
    properties: list[PlatformProperty] | None = None


class SignalNode(PlatformNode):
    name: str
    referenceId: str
    parentIdPath: str = Field(min_length=1)
    referenceObject: SignalReference
    inheritedProperties: list[InheritedPlatformProperty] | None = None


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


class PropertyFilter(BaseModel):
    """A condition on a property of signals, see "Property filters" in the documentation"""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    condition: Literal["equals", "any", "all", "exists"] = "equals"
    value: str | bool | int | float | list[str] | None = None

    @model_validator(mode="after")
    def value_fits_condition(self) -> Self:
        if self.condition == "equals" and (self.value is None or isinstance(self.value, list)):
            raise ValueError(
                "condition 'equals' requires a single value (a string, number or boolean)"
            )
        if self.condition in ("any", "all") and len(self.items()) == 0:
            raise ValueError(
                f"condition '{self.condition}' requires a comma-separated string or a list of"
                " strings with at least one non-empty item as value"
            )
        return self

    def items(self) -> list[str]:
        """The value items for the conditions any and all"""
        if self.value is None:
            return []
        values = self.value if isinstance(self.value, list) else str(self.value).split(",")
        return [item.strip() for item in values if item.strip() != ""]


def collect_property_filters(
    property_label, property_condition, property_value, property_filters
) -> list[PropertyFilter]:
    """Validate the property filter inputs, returning all property filters

    Raises ComponentInputValidationException for invalid property filter inputs.
    """
    single_filter_inputs = ["property_label", "property_condition", "property_value"]
    collected = []
    if property_label is not None:
        try:
            collected.append(
                PropertyFilter(
                    label=property_label,
                    condition=property_condition if property_condition is not None else "equals",
                    value=property_value,
                )
            )
        except ValidationError as e:
            raise ComponentInputValidationException(
                "Invalid property filter given by property_label, property_condition and"
                f" property_value: {format_validation_error(e, 'property filter')}",
                invalid_component_inputs=single_filter_inputs,
            ) from e
    elif property_value is not None or property_condition not in (None, "equals"):
        raise ComponentInputValidationException(
            "property_condition and property_value require property_label to be set.",
            invalid_component_inputs=single_filter_inputs,
        )

    if property_filters is not None:
        try:
            collected += TypeAdapter(list[PropertyFilter]).validate_python(
                [property_filters] if isinstance(property_filters, dict) else property_filters
            )
        except ValidationError as e:
            raise ComponentInputValidationException(
                "Invalid property_filters, expected a list of objects with keys label,"
                f" condition and value: {format_validation_error(e, 'property_filters')}",
                invalid_component_inputs=["property_filters"],
            ) from e
    return collected


def has_value(value) -> bool:
    """Whether a property value is actually set

    As in hetida platform, null or a blank string means "not set here, inherit from above"
    and not an explicitely empty value.
    """
    return value is not None and str(value).strip() != ""


def to_correct_value_type(prop):
    """Convert property value according to its type

    Returns None if the property has no value. Raises ValueError or TypeError if the value
    cannot be converted.
    """
    value = prop.get("value")
    if not has_value(value):
        return None

    prop_type = (prop.get("type") or "").upper()

    if prop_type == "FLOAT":
        return float(value)
    if prop_type in {"INT", "INTEGER"}:
        if isinstance(value, float) and not value.is_integer():
            raise ValueError("not an integer")  # int() would silently truncate
        return int(value)
    if prop_type in {"BOOL", "BOOLEAN"}:
        if isinstance(value, bool):
            return value
        if str(value).strip().lower() not in {"true", "false"}:
            raise ValueError("expected true or false")
        return str(value).strip().lower() == "true"

    # everything else (string, timestamps, ...) to be left as it is: probably string
    return value


def effective_property(child, label: str):
    """The effective property of a signal node: own one with value, else inherited one with value

    Returns None if the signal has no effective value for the property.
    """
    own_properties = child["referenceObject"].get("properties") or []
    inherited_properties = child.get("inheritedProperties") or []
    for prop in [*own_properties, *inherited_properties]:
        if prop.get("label") == label and has_value(prop.get("value")):
            return prop
    return None


def as_comparable_string(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value).strip()


def property_value_equals(prop, filter_value, child) -> bool:
    """Compare a property with the value of an "equals" property filter respecting its type"""
    try:
        node_value = to_correct_value_type(prop)
    except (ValueError, TypeError) as e:
        origin = (
            f", inherited from '{prop.get('inheritedFromName')}'"
            f" (node id {prop.get('inheritedFromNodeId')})"
            if "inheritedFromNodeId" in prop
            else ""
        )
        raise ValueError(
            f"Cannot convert value {prop.get('value')!r} of property '{prop.get('label')}'"
            f" (type {prop.get('type')}) of signal '{child['name']}'"
            f" (node id {child['id']}){origin}: {e}"
        ) from e

    prop_type = (prop.get("type") or "").upper()
    if prop_type in {"FLOAT", "INT", "INTEGER", "BOOL", "BOOLEAN"}:
        try:
            return to_correct_value_type({"type": prop_type, "value": filter_value}) == node_value
        except ValueError, TypeError:
            return False  # filter value not representable in the property's type
    if prop_type == "DATE":
        try:
            return bool(pd.Timestamp(filter_value) == pd.Timestamp(node_value))
        except ValueError, TypeError:
            pass  # compare as strings
    return as_comparable_string(filter_value) == as_comparable_string(node_value)


def property_filter_applies(property_filter: PropertyFilter, child) -> bool:
    prop = effective_property(child, property_filter.label)
    if prop is None:
        return False
    if property_filter.condition == "exists":
        return True
    if property_filter.condition == "equals":
        return property_value_equals(prop, property_filter.value, child)

    property_items = [item.strip() for item in str(prop["value"]).split(",")]
    matches = [item in property_items for item in property_filter.items()]
    return all(matches) if property_filter.condition == "all" else any(matches)


def filter_by_properties(signal_children, property_filters: list[PropertyFilter]):
    """Keep only signals to which all property filters apply"""
    for property_filter in property_filters:
        signal_children = [
            child for child in signal_children if property_filter_applies(property_filter, child)
        ]
    return signal_children


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


def metric_values_by_signal_id(signal_children, use_as_metric):
    """Values of the use_as_metric field of the signals for the metric column

    Determined from the hierarchy, since they are needed before loading the data. "external_id"
    of the metadata provided by the adapter is called "externalTimeSeriesId" there.

    Raises ValueError if a signal has no value or the values are not unique.
    """
    reference_field = "externalTimeSeriesId" if use_as_metric == "external_id" else use_as_metric
    if reference_field in SIGNAL_REFERENCE_PLATFORM_FIELDS:
        ensure_signal_reference_field(signal_children, reference_field, "as use_as_metric")
    metric_mapping_dict = {
        child["referenceId"]: (
            # "id" is always the signal id (not the node id), independent of the referenceObject
            child["referenceId"]
            if use_as_metric == "id"
            else child["referenceObject"].get(reference_field, child.get(reference_field))
        )
        for child in signal_children
    }

    missing_metric_values = [
        f"'{child['name']}' (id {child['referenceId']})"
        for child in signal_children
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

    return metric_mapping_dict


def metric_metadata(attrs_from_adapter, signal_id, metric_key, metric_value):
    """Metric metadata of a loaded signal as provided by the hetida platform adapter

    attrs_from_adapter maps the ids of the loaded signals to their metadata, which the adapter
    provides following the hetida designer metadata conventions for a SERIES: The metadata of a
    signal is its single entry under "metrics", identified via dataset_metadata.metric_key.

    metric_value is the value used for this signal in the metric column. It is set under
    metric_key, so that metadata can be matched to the data via dataset_metadata.metric_key,
    even if the adapter does not provide this field (e.g. relativeNamePath).

    Raises HetidaPlatformResponseError if the adapter provides no metadata for the signal.
    """
    signal_attrs = attrs_from_adapter.get(signal_id) or {}
    adapter_metric_key = (signal_attrs.get("dataset_metadata") or {}).get("metric_key") or "id"
    signal_metrics = [
        metric
        for metric in signal_attrs.get("metrics") or []
        if metric.get(adapter_metric_key) == signal_id
    ]
    if len(signal_metrics) != 1:
        raise HetidaPlatformResponseError(
            f"hetida platform provided no metadata for signal {signal_id} when loading its data."
            " This requires a hetida platform version providing the metadata following the"
            " hetida designer metadata conventions (hetida platform 2603.1012 or newer)."
        )

    metric = deepcopy(signal_metrics[0])
    metric[metric_key] = metric_value
    return metric


def warn_about_metadata_convention_issues(attrs_from_adapter, signal_children) -> None:
    """Log a warning for each signal whose metadata does not adhere to the metadata conventions

    Skipped if the runtime validates the metadata received from the hetida platform adapter
    itself (GENERIC_REST_ADAPTER_METADATA_VALIDATION), which then logs the issues or lets
    loading fail.
    """
    validation_mode = get_config().generic_rest_adapter_metadata_validation.get(
        HETIDA_PLATFORM_ADAPTER_KEY, MetadataValidationMode.OFF
    )
    if validation_mode != MetadataValidationMode.OFF:
        return

    for child in signal_children:
        issues = check_metadata_conventions(
            attrs_from_adapter.get(child["referenceId"]) or {}, "SERIES"
        )
        if len(issues) > 0:
            logger.warning(
                "Metadata provided by hetida platform for signal '%s' (id %s) does not adhere"
                " to the metadata conventions. Found issues:\n%s",
                child["name"],
                child["referenceId"],
                "\n".join(
                    f"* {issue.severity} at {issue.location or 'top level'}: {issue.message}"
                    for issue in issues
                ),
            )


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
        "property_label": {"data_type": "STRING", "default_value": None},
        "property_condition": {"data_type": "STRING", "default_value": "equals"},
        "property_value": {"data_type": "ANY", "default_value": None},
        "property_filters": {"data_type": "ANY", "default_value": None},
        "include_ingestion_signals": {"data_type": "BOOLEAN", "default_value": True},
        "include_virtual_signals": {"data_type": "BOOLEAN", "default_value": True},
        "use_as_metric": {"data_type": "STRING", "default_value": "external_id"},
    },
    "outputs": {
        "ts_data": {"data_type": "MULTITSFRAME"},
    },
    "name": "Hetida Platform Signal Timeseries Data",
    "category": "hetida platform Sources",
    "description": "Load multiple signal timeseries data from hetida platform",
    "version_tag": "0.1.12",
    "id": "329b1f21-b8aa-4c80-bb5f-8fa1dcae75ef",
    "revision_group_id": "c8c22f6a-b046-4c50-9364-5cbb517cfb97",
    "state": "RELEASED",
    "released_timestamp": "2026-10-20T14:59:50.510720+00:00",
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
    property_label=None,
    property_condition="equals",
    property_value=parse_default_value(COMPONENT_INFO, "property_value"),
    property_filters=parse_default_value(COMPONENT_INFO, "property_filters"),
    include_ingestion_signals=True,
    include_virtual_signals=True,
    use_as_metric="external_id",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    platform_api_url = get_platform_api_url()

    asset_node_id = ensure_asset_node_id(asset_node_id)

    allowed_measurements = validate_measurement(measurement)
    property_filters = collect_property_filters(
        property_label, property_condition, property_value, property_filters
    )

    start, end = resolve_interval(timestampFrom, timestampTo)

    # Obtain and filter children
    all_children = validate_node_children(
        await fetch_node_children(
            platform_api_url,
            asset_node_id,
            params={
                "recursive": recursive,
                # inherited property values are only needed for property filters:
                "withInheritedProperties": len(property_filters) > 0,
            },
        )
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

    selected_children = filter_by_properties(selected_children, property_filters)

    # Determine the values for the metric column and check them before loading any data
    metric_mapping_dict = metric_values_by_signal_id(selected_children, use_as_metric)

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
            metric_metadata(
                attrs_from_adapter,
                child["referenceId"],
                metric_key=use_as_metric,
                metric_value=metric_mapping_dict[child["referenceId"]],
            )
            for child in selected_children
        ],
    }

    warn_about_metadata_convention_issues(attrs_from_adapter, selected_children)

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


# Testing
try:
    import pytest
except ImportError:
    pass
else:
    SIGNAL_ID = "7ab8c419-8745-4714-b588-57c0c772cc95"

    @pytest.fixture
    def attrs_from_adapter():
        # as the hetida platform adapter provides them for a SERIES read
        return {
            SIGNAL_ID: {
                "dataset_metadata": {
                    "metric_key": "id",
                    "single_metric": SIGNAL_ID,
                    "queried_metrics": [SIGNAL_ID],
                    "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
                    "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
                    "ref_interval_type": "closed",
                },
                "metrics": [
                    {
                        "id": SIGNAL_ID,
                        "external_id": "water.north.level",
                        "name": "Water level north",
                        "display_name": None,
                        "description": "Level at the northern gauge",
                        "inherited": {"site": "north", "signal_role": "level"},
                        "comments": [
                            {
                                "id": "0b5f0f0e-6d1c-4f7e-9a51-1f3c2a9e8d11",
                                "start_date": "2026-10-18T06:00:00Z",
                                "end_date": "2026-10-18T07:30:00Z",
                                "created_at": "2026-10-18T08:12:45.123Z",
                                "edited_at": None,
                                "content": "Gauge maintenance",
                                "username": "jdoe",
                                "tags": ["maintenance"],
                                "replies": [],
                            }
                        ],
                        "value_dimensions": [
                            {
                                "column": "value",
                                "name": "Water level north",
                                "unit": "m",
                                "measurement": "level",
                                "value_data_type": "float",
                            }
                        ],
                        "default_aggregation_method": "AVG",
                    }
                ],
            }
        }

    def signal_child(signal_id, external_time_series_id):
        return {
            "id": f"node of {signal_id}",
            "referenceId": signal_id,
            "name": f"name of {signal_id}",
            "relativeNamePath": f"Asset/name of {signal_id}",
            "referenceObject": {"id": signal_id, "externalTimeSeriesId": external_time_series_id},
        }

    @pytest.mark.parametrize(
        ("use_as_metric", "expected_values"),
        [
            ("external_id", ["ts.a", "ts.b"]),
            ("externalTimeSeriesId", ["ts.a", "ts.b"]),
            ("id", ["a", "b"]),
            ("relativeNamePath", ["Asset/name of a", "Asset/name of b"]),
        ],
    )
    def test_metric_values(use_as_metric, expected_values):
        children = [signal_child("a", "ts.a"), signal_child("b", "ts.b")]

        assert metric_values_by_signal_id(children, use_as_metric) == dict(  # noqa: S101
            zip(["a", "b"], expected_values, strict=True)
        )

    @pytest.mark.parametrize(
        ("external_time_series_ids", "message"),
        [(["ts.a", "ts.a"], "duplicates"), (["ts.a", None], "no value")],
    )
    def test_invalid_metric_values(external_time_series_ids, message):
        children = [
            signal_child(signal_id, external_time_series_id)
            for signal_id, external_time_series_id in zip(
                ["a", "b"], external_time_series_ids, strict=True
            )
        ]

        with pytest.raises(ValueError, match=message):
            metric_values_by_signal_id(children, "external_id")

    def test_metric_metadata_is_adapter_metadata_with_metric_value(attrs_from_adapter):
        metric = metric_metadata(
            attrs_from_adapter,
            SIGNAL_ID,
            metric_key="relativeNamePath",
            metric_value="Pegel Nord/Water-lvl-north",
        )

        assert metric == attrs_from_adapter[SIGNAL_ID]["metrics"][0] | {  # noqa: S101
            "relativeNamePath": "Pegel Nord/Water-lvl-north"
        }
        # the adapter metadata is copied, not referenced
        attrs_from_adapter[SIGNAL_ID]["metrics"][0]["comments"].clear()
        assert len(metric["comments"]) == 1  # noqa: S101

    def test_metric_value_takes_precedence_over_adapter_metadata(attrs_from_adapter):
        metric = metric_metadata(
            attrs_from_adapter, SIGNAL_ID, metric_key="name", metric_value="Water-lvl-north"
        )

        assert metric["name"] == "Water-lvl-north"  # noqa: S101

    @pytest.mark.parametrize(
        "attrs_from_adapter",
        [
            {},
            {SIGNAL_ID: {}},
            {SIGNAL_ID: {"metrics": [{"id": "another signal"}]}},
            # metadata format of hetida platform versions before 2603.1012
            {SIGNAL_ID: {"single_metric_metadata": {"structured_metadata": {"inherited": {}}}}},
        ],
    )
    def test_missing_adapter_metadata_raises(attrs_from_adapter):
        with pytest.raises(HetidaPlatformResponseError, match="no metadata for signal"):
            metric_metadata(attrs_from_adapter, SIGNAL_ID, metric_key="id", metric_value=SIGNAL_ID)

    def test_metadata_follows_metadata_conventions(attrs_from_adapter):
        multitsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2026-10-18T06:00:00Z"]),
                "metric": ["water.north.level"],
                "value": [2.5],
            }
        )
        multitsframe.attrs = {
            "dataset_metadata": {
                "metric_key": "external_id",
                "queried_metrics": ["water.north.level"],
                "ref_interval_start_timestamp": "2026-10-18T00:00:00+00:00",
                "ref_interval_end_timestamp": "2026-10-19T00:00:00+00:00",
                "ref_interval_type": "closed",
            },
            "metrics": [
                metric_metadata(
                    attrs_from_adapter,
                    SIGNAL_ID,
                    metric_key="external_id",
                    metric_value="water.north.level",
                )
            ],
        }

        assert check_metadata_conventions(multitsframe) == []  # noqa: S101

    def test_no_warning_for_metadata_following_conventions(attrs_from_adapter, caplog, monkeypatch):
        monkeypatch.setattr(get_config(), "generic_rest_adapter_metadata_validation", {})

        with caplog.at_level(logging.WARNING):
            warn_about_metadata_convention_issues(
                attrs_from_adapter, [signal_child(SIGNAL_ID, "water.north.level")]
            )

        assert caplog.records == []  # noqa: S101

    @pytest.mark.parametrize(
        "runtime_validation",
        [
            {},
            {HETIDA_PLATFORM_ADAPTER_KEY: MetadataValidationMode.OFF},
            {"another-adapter": MetadataValidationMode.ERROR},
        ],
    )
    def test_warning_for_metadata_not_following_conventions(
        runtime_validation, attrs_from_adapter, caplog, monkeypatch
    ):
        monkeypatch.setattr(
            get_config(), "generic_rest_adapter_metadata_validation", runtime_validation
        )
        del attrs_from_adapter[SIGNAL_ID]["metrics"][0]["value_dimensions"][0]["unit"]

        with caplog.at_level(logging.WARNING):
            warn_about_metadata_convention_issues(
                attrs_from_adapter, [signal_child(SIGNAL_ID, "water.north.level")]
            )

        assert len(caplog.records) == 1  # noqa: S101
        message = caplog.records[0].getMessage()
        assert f"signal 'name of {SIGNAL_ID}' (id {SIGNAL_ID})" in message  # noqa: S101
        assert "* error at metrics[0].value_dimensions[0].unit:" in message  # noqa: S101

    @pytest.mark.parametrize(
        "validation_mode", [MetadataValidationMode.WARN, MetadataValidationMode.ERROR]
    )
    def test_no_check_if_runtime_validates_metadata(
        validation_mode, attrs_from_adapter, caplog, monkeypatch
    ):
        monkeypatch.setattr(
            get_config(),
            "generic_rest_adapter_metadata_validation",
            {HETIDA_PLATFORM_ADAPTER_KEY: validation_mode},
        )
        del attrs_from_adapter[SIGNAL_ID]["metrics"][0]["value_dimensions"][0]["unit"]

        with caplog.at_level(logging.WARNING):
            warn_about_metadata_convention_issues(
                attrs_from_adapter, [signal_child(SIGNAL_ID, "water.north.level")]
            )

        assert caplog.records == []  # noqa: S101


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
            "workflow_input_name": "property_label",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "property_condition",
            "use_default_value": True,
            "filters": {"value": "equals"},
        },
        {
            "workflow_input_name": "property_value",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "property_filters",
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
            "workflow_input_name": "property_label",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "property_condition",
            "use_default_value": True,
            "filters": {"value": "equals"},
        },
        {
            "workflow_input_name": "property_value",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "property_filters",
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
