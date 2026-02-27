"""Documentation for Hetida Platform Channel Timeseries Data

# Hetida Platform Channel Timeseries Data

## Description
This component is meant to be used via the [component adapter](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/component_adapter.md) via [URI Wirings](https://github.com/hetida/hetida-designer/blob/release/docs/execution/uri_wirings.md) in [hetida platform](https://hetida.io/). It enables fetching timeseries data of dynamically resolved collections of multiple hetida platform channels into a MULTITSFRAME.

As an example, you might want to load all timeseries data of those channels under a certain asset in your hierarchy, that represent an energy consumption measurement, e.g. in order to sum them up.

Note that typically a URI Wiring shortcut `hd://timeseries` points to the newest revision of this component.

## Inputs
* **asset_node_id** (str, optional, default value `None`): Asset node id. If None, will be inferred from execution context which the hetida platform provides: The parent asset of the currently executed virtual channel or workflow configuration. If not provided either way, a ValueError will be raised.
* **timestampFrom** (str): Isoformat timestamp or [dtexp](https://github.com/stewit/dtexp) expression defining start of interval to load. hetida platform will provide this automatically, but it can be overriden through an explicit value.
* **timestampTo** (str):  Isoformat timestamp or [dtexp](https://github.com/stewit/dtexp) expression defining end of interval to load. hetida platform will provide this automatically, but it can be overriden through an explicit value.
* **recursive** (bool, optional, default value True): If True channels are collected recursively. If False, only channels directly under the asset of `asset_node_id` are considered.
* **starts_with** (str, optional, default value None): If set, restrict to channels with name starting with this string. Case-sensitive.
* **name_regexp** (str, optional, default value None). If not None, only channels whose name match the provided regexp will be considered.
* **relative_name_path_regexp** (str, optional, default value None). If not None, only channels whose explorer "relative name path" match the provided regexp will be considered.
* **measurement** (ANY, expects str or list of strings, optional, default value `None`): Either a single string or an array of strings or null. If not null, only channels having one of the provided measurements are collected.
* **include_ingestion_channels** (bool, optional, default value True): Whether ingestion channels should be included
* **include_virtual_channels** (bool, optional, default value True): Whether virtual channels should be included
* **use_as_metric** (str, optional, default value "externalTimeSeriesId"): Which field of the channel is used to identify its metric. In the resulting multitsframe this will define what is used in the metric column. Make sure to select a field with unique value per metric (e.g. "id"). Note that the values "externalTimeSeriesId" or "relativeNamePath", while being more verbose, do not necessarily have to be unique. The component aborts with a ValueError if the selected field does not uniquely identify the actually loaded metrics.

## Outputs

* **ts_data** (Multitsframe): Contains the loaded timeseries data.

## Details

For trafos employed via the hetida platform at a specific point in its asset hierarchy, e.g. in virtual channels or workflow configurations, it automatically infers the current asset node id from the invocation context and collects data from there. In hetida platform you typically employ it using an URI wiring in such a configuration.

Requires the env variable `HETIDA_PLATFORM_API_URL` to be set for the designer runtime to point to the hetida platform core api, e.g. "http://test-hetida-platform-core-backend-svc:8080/api" in a K8S setup or "http://core-backend:8080/api" in a docker-compose setup.

Since it uses the hetida platform hetida designer adapter REST service to fetch data it requires the runtime to know its adapter key and expects this adapter [to be configured](https://github.com/hetida/hetida-designer/blob/release/docs/adapter_system/adapter_registration.md) for the runtime service. If the adapter key differs from `hetida-platform-adapter` it must be configured for the runtime using the `HETIDA_PLATFORM_ADAPTER_KEY` environment variable.

Metadata will be present in the resulting DataFrame's attrs attribute, following hetida designer [metadata conventions](https://github.com/hetida/hetida-designer/blob/release/docs/metadata_attrs.md).

You may also use this component as a good starting point to write your own variant for dynamical selection of channel timeseries data which fits your specific hetida platform setup and use cases.

## Examples

E.g. the URI wiring
```
hd://component-adapter/<ID_OF_THIS_COMPONENT>?measurement=energyconsumption?include_virtual_channels=false
```
or
```
hd://timeseries?measurement=energyconsumption?include_virtual_channels=false
```

will load all ingestion channels (but not virtual channels) that have "energyconsumption" configured as measurement.
"""

import logging
import os
import re
from collections import defaultdict
from copy import deepcopy
from posixpath import join as posix_urljoin

import httpx
import pandas as pd

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_ts_data import load_ts_data_from_adapter
from hetdesrun.dt_utils import resolve_interval
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.runtime.context import (
    get_hierarchy_object_info,
)
from hetdesrun.webservice.auth_dependency import get_auth_headers

logger = logging.getLogger(__name__)

PLATFORM_API_URL = os.environ.get("HETIDA_PLATFORM_API_URL")

HETIDA_PLATFORM_ADAPTER_KEY = os.environ.get(
    "HETIDA_PLATFORM_ADAPTER_KEY", "hetida-platform-adapter"
)
EXPLORER_SEP_CHAR = "/"


async def get_external_auth_headers():
    return await get_auth_headers(external=True)


def ensure_asset_node_id(asset_node_id: str | None) -> str:
    """Ensure asset node id is present, trying to load from context if not provided explicitely

    Raises ValueError if id is neither provided directly nor available in context.
    """
    if asset_node_id is None:
        hierarchy_object = get_hierarchy_object_info()

        logger.debug("Loaded hierarchy object: %s", str(hierarchy_object))

        # Do we need other attributes: id, node_id, parent_node_id, type?
        if hierarchy_object.parent_node_id is None:
            raise ValueError("No asset id provided: Neither directly nor by context.")

        asset_node_id = str(hierarchy_object.parent_node_id)
        logger.debug(
            "Using asset node id from hierarchy_object provided via context: %s",
            asset_node_id,
        )
    else:
        logger.debug("Using asset_node_id provided directly from input: %s", asset_node_id)
    return asset_node_id


def metric_metadata_from_child(child, attrs_from_adapter):
    """Built metric metadata from hierarchy object"""

    metric_object = deepcopy(child["referenceObject"])
    metric_object.pop("schedulerJob", None)
    metric_object.pop("outputDefinitions", None)
    metric_object["hierarchy_object"] = child

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
        "include_ingestion_channels": {"data_type": "BOOLEAN", "default_value": True},
        "include_virtual_channels": {"data_type": "BOOLEAN", "default_value": True},
        "use_as_metric": {
            "data_type": "STRING",
            "default_value": "externalTimeSeriesId",
        },
    },
    "outputs": {
        "ts_data": {"data_type": "MULTITSFRAME"},
    },
    "name": "Hetida Platform Channel Timeseries Data",
    "category": "hetida platform Sources",
    "description": "Load multiple channel timeseries data from hetida platform",
    "version_tag": "0.1.9",
    "id": "c6378f34-6038-4127-b829-19bcd9bd405b",
    "revision_group_id": "c8c22f6a-b046-4c50-9364-5cbb517cfb97",
    "state": "RELEASED",
    "released_timestamp": "2026-02-26T21:12:06.748882+00:00",
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
    include_ingestion_channels=True,
    include_virtual_channels=True,
    use_as_metric="externalTimeSeriesId",
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    asset_node_id = ensure_asset_node_id(asset_node_id)

    start, end = resolve_interval(timestampFrom, timestampTo)

    # Obtain and filter children
    children_url = posix_urljoin(PLATFORM_API_URL, "nodes", asset_node_id, "children")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            children_url,
            headers=await get_external_auth_headers(),
            params={"recursive": "true"},
        )

    if resp.status_code != 200:
        msg = f"Request getting asset node children failed with status code: {resp.status_code}"
        logger.error(msg)
        resp.raise_for_status()

    resp = httpx.get(
        children_url,
        headers=await get_external_auth_headers(),
        params={"recursive": recursive},
    )
    resp.raise_for_status()

    all_children = resp.json()

    channel_children = [
        child
        for child in all_children
        if (
            child["nodeType"] == "CHANNEL"
            and (include_ingestion_channels or (include_ingestion_channels is None))
        )
        or (
            child["nodeType"] == "VIRTUAL_CHANNEL"
            and (include_virtual_channels or (include_virtual_channels is None))
        )
    ]

    selected_children = channel_children

    id_name_dict = {child["id"]: child["name"] for child in all_children}
    for child in selected_children:
        id_path_parts_from_root = child["parentIdPath"].split("_")[::-1]
        asset_node_id_index = id_path_parts_from_root.index(asset_node_id)
        child["relativeNamePath"] = EXPLORER_SEP_CHAR.join(
            [
                id_name_dict.get(part, "NO NAME AVAILABLE")
                for part in id_path_parts_from_root[asset_node_id_index + 1 :]
            ]
            + [child["name"]]
        )

    # Filter by measurement
    if measurement is not None:
        allowed_measurements = set(measurement) if isinstance(measurement, list) else {measurement}

        selected_children = [
            child
            for child in selected_children
            if (child_measurement := child["referenceObject"]["measurement"]) is not None
            and child_measurement in allowed_measurements
        ]

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

    if len(selected_children) == 0:
        logger.info("No children selected at all for loading channel data.")
        loaded_ts_data = pd.DataFrame()

    else:
        # Load data from adapter timeseries endpoint
        loaded_ts_data = await load_ts_data_from_adapter(
            filtered_sources=[
                FilteredSource(
                    ref_id=child["referenceObject"][
                        "id"
                    ],  # channel id => will become timeseriesId column
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
        loaded_ts_data.attres = attrs

    # metric column
    loaded_ts_data.rename(
        columns={"timeseriesId": "metric"},
        inplace=True,  # noqa:PD002
    )

    # At this point, "id" of child["referenceObject"] is used in the data in metric column
    # Now we transform the data to use the field specified by use_as_metric instead!

    metric_mapping_dict = {
        child["referenceObject"]["id"]: child["referenceObject"].get(
            use_as_metric, child.get(use_as_metric)
        )
        for child in selected_children
    }

    value_to_keys = defaultdict(list)
    for key, value in metric_mapping_dict.items():
        value_to_keys[value].append(key)
    duplicates = {val: keys for val, keys in value_to_keys.items() if len(keys) > 1}
    if len(duplicates) > 0:
        raise ValueError(
            f"The selected {use_as_metric=} has {duplicates=} for the loaded metrics. Aborting."
        )

    loaded_ts_data["metric"] = loaded_ts_data["metric"].map(metric_mapping_dict)

    # Set metadata accordingly

    attrs_from_adapter = loaded_ts_data.attrs

    loaded_ts_data.attrs = {
        "dataset_metadata": {
            "metric_key": use_as_metric,
            "queried_metrics": [
                child["referenceObject"].get(use_as_metric, child.get(use_as_metric))
                for child in selected_children
            ],
            "ref_interval_start_timestamp": start.isoformat(),
            "ref_interval_end_timestamp": end.isoformat(),
            "ref_interval_type": "closed",
        },
        "metrics": [
            metric_metadata_from_child(child, attrs_from_adapter) for child in selected_children
        ],
    }

    # log loaded data per timeseries

    loaded_data_points_per_metric = {
        metric_mapping_dict[channel_id := child["referenceObject"]["id"]]: len(
            loaded_ts_data[loaded_ts_data.metric == metric_mapping_dict[channel_id]]
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
            "workflow_input_name": "include_ingestion_channels",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "include_virtual_channels",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "use_as_metric",
            "filters": {"value": "relativeNamePath"},
        },
    ]
}
RELEASE_WIRING = TEST_WIRING_FROM_PY_FILE_IMPORT = {
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
            "workflow_input_name": "include_ingestion_channels",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "include_virtual_channels",
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
            "workflow_input_name": "include_ingestion_channels",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "include_virtual_channels",
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
