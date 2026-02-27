"""Documentation for Hetida Platform Assets

# Hetida Platform Assets


## Description
This component is meant to be used via the component adapter. If hetida designer is running as part of the hetida platform it enables fetching asset data together with their metadata / properties from the asset hierarchy. For trafos employed via the hetida platform at a specific point in the hierarchy, it automatically infers the parent asset node id from the invocation context.

Requires the env variable `HETIDA_PLATFORM_API_URL` to be set to the hetida platform core api, e.g. "http://test-hetida-platform-core-backend-svc:8080/api" in a K8S setup for the designer runtime or "http://core-backend:8080/api" in a docker-compose setup.

E.g. if you want to provide a map plot with all assets below a certain asset in the hierarchy marked on the map you can fetch the relevant assets using this component and use "latitude" / "longitude" dynamic properties of your asset type. This component would then be used as component adapter source for the respective map plot component you write.

## Inputs

* "asset_node_id" ({"data_type": "STRING", "default_value": None}): The asset node id of the parent asset. If not set it is tried to obtain it from context. If neither provides it, a ValueError is raised
* "starts_with": {"data_type": "STRING", "default_value": None}: Allows to filter assets by beginning of their name. Filtering is case-insensitive.
* "recursive": {"data_type": "BOOLEAN", "default_value": True}: Whether child assets are collected recursively.
* "attach_properties": {"data_type": "ANY", "default_value": None}: Can be a list / json array of property names. If that's the case these property values are explicitely added as columns (even if no asset has this property). For assets not having a property the value will be null.
* "attach_all_properties": {"data_type": "BOOLEAN", "default_value": True}: This attaches all properties that actually occur somewhere in the selected asset children as a new column. If a property does not occur, it won't be added as column.
* "drop_ref_obj_column": {"data_type": "BOOLEAN", "default_value": True}: Whether the ref object column (from which properties are collected) should be excluded from the final dataframe.
* "name_regexp": {"data_type": "STRING", "default_value": None}: If set, filter for assets with name matching the provided regexp.


## Outputs
* "assets": {"data_type": "DATAFRAME"}: Dataframe with one asset per row with columns like "name", "id", "assetType.name", "parentId", "parentName" and more with addtional columns for the properties if requested.

## Details
* Does not include the asset note from asset_node_id, i.e. the overall parent, only children (recursively, if requested).
* If you want to ensure that a property column is there you cannot rely on automatic property addition (`attach_all_properties`): If property never occurs, it will not be added as column. Instead you have to explicitely request the property by setting e.g `attach_properties` to something like `["my_property"]`.

## Examples

Output may e.g. look like (hetida designer dataframe json):

```
{
  "__hd_wrapped_data_object__": "DATAFRAME",
  "__metadata__": {},
  "__data__": {
    "id": {
      "0": "23e503af-d05a-45c7-bf25-060a4900782e",
      "1": "4bd32e3b-4426-4193-b60a-298e1b7ae8b7",
      "2": "7af1a6ae-5268-48fb-b659-a1f81d6f1206",
      "3": "196854bf-ca4b-4906-9036-5ce143c883f2",
      "4": "b6978430-f477-47d7-bb0e-838336f7aaec",
      "5": "206c829a-d591-4c09-978b-84581ee33fe1"
    },
    "parentId": {
      "0": "3cbf482e-990f-4e39-8b8c-95c25a1333cd",
      "1": "3cbf482e-990f-4e39-8b8c-95c25a1333cd",
      "2": "3cbf482e-990f-4e39-8b8c-95c25a1333cd",
      "3": "7af1a6ae-5268-48fb-b659-a1f81d6f1206",
      "4": "3cbf482e-990f-4e39-8b8c-95c25a1333cd",
      "5": "3cbf482e-990f-4e39-8b8c-95c25a1333cd"
    },
    "parentName": {
      "0": "Main Area",
      "1": "Main Area",
      "2": "Main Area",
      "3": "Sour field area",
      "4": "Main Area",
      "5": "Main Area"
    },
    "referenceId": {
      "0": "c01ae76c-e122-4367-b90e-3c03b5e53cff",
      "1": "26ac3a74-241e-46b7-9005-9903bdd5ece9",
      "2": "252d699d-f9e0-47c2-ad1c-b9cceb00723c",
      "3": "767f9bf1-ba26-4ff4-9298-98180d67b9e9",
      "4": "d3739694-ad60-4794-bcc8-57108c1a1cf3",
      "5": "a25b135f-04a3-43c0-bd53-c0a2089fd0dc"
    },
    "name": {
      "0": "South Plant",
      "1": "Other plant",
      "2": "Sour field plant",
      "3": "Oak creek plant",
      "4": "Horn castle plant",
      "5": "Small plant"
    },
    "nodeType": {
      "0": "ASSET",
      "1": "ASSET",
      "2": "ASSET",
      "3": "ASSET",
      "4": "ASSET",
      "5": "ASSET"
    },
    "icon": {
      "0": "home",
      "1": "home",
      "2": "folder",
      "3": "home",
      "4": "home",
      "5": "home"
    },
    "description": {
      "0": null,
      "1": null,
      "2": null,
      "3": "Some description",
      "4": "Some description",
      "5": null
    },
    "hasChildren": {
      "0": true,
      "1": true,
      "2": true,
      "3": true,
      "4": false,
      "5": false
    },
    "parentIdPath": {
      "0": "3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9",
      "1": "3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9",
      "2": "3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9",
      "3": "7af1a6ae-5268-48fb-b659-a1f81d6f1206_3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9",
      "4": "3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9",
      "5": "3cbf482e-990f-4e39-8b8c-95c25a1333cd_646e2593-996c-4f60-b591-bceed1e4010b_b03a7c72-8a0b-4016-9a12-7b71af99f0f9"
    },
    "isEditable": {
      "0": true,
      "1": true,
      "2": true,
      "3": true,
      "4": true,
      "5": true
    },
    "isDeletable": {
      "0": true,
      "1": true,
      "2": true,
      "3": true,
      "4": true,
      "5": true
    },
    "onlyUsedToShowChildElement": {
      "0": false,
      "1": false,
      "2": false,
      "3": false,
      "4": false,
      "5": false
    },
    "assetType.name": {
      "0": "Plant with capacity",
      "1": "Plant with capacity",
      "2": "Directory",
      "3": "Plant with capacity",
      "4": "Plant with capacity",
      "5": "Plant with capacity"
    },
    "capacity": {
      "0": 550.2,
      "1": 689,
      "2": null,
      "3": 403.2,
      "4": 55,
      "5": 35
    },
    "latitude": {
      "0": "51.454617",
      "1": "51.472113940382734",
      "2": null,
      "3": "51.46805648765847",
      "4": "51.45782413163731",
      "5": "51.44490567804898"
    },
    "longitude": {
      "0": "7.163409424444822",
      "1": "7.144091264578399",
      "2": null,
      "3": "7.170650757618759",
      "4": "7.1485711255043265",
      "5": "7.140732055633175"
    }
  }
}

```
"""

import logging
import os
import re
from posixpath import join as posix_urljoin

import httpx
import pandas as pd

from hetdesrun.runtime.context import get_hierarchy_object_info
from hetdesrun.webservice.auth_dependency import get_auth_headers

logger = logging.getLogger(__name__)

PLATFORM_API_URL = os.environ.get("HETIDA_PLATFORM_API_URL")


async def get_external_auth_headers():
    return await get_auth_headers(external=True)


def to_correct_value_type(prop):
    prop_type = prop["type"]

    if prop_type.upper() == "FLOAT":
        return float(prop["value"])
    if prop_type.upper() in {"INT", "INTEGER"}:
        return int(prop["value"])
    if prop_type.upper() in {"BOOL", "BOOLEAN"}:
        return bool(prop["value"])

    # everything else (string, timestamps, ...) to be left as it is: probably string
    return prop["value"]


def extract_property_value(ref_obj, property_name: str):
    """Extract a single property by its name from the ref object

    Returns None if the property cannot be found.
    """
    properties = [y for y in ref_obj["properties"] if y["label"] == property_name]

    if len(properties) > 1:
        raise ValueError(f"Found property {property_name} more than once!")
    if len(properties) == 0:
        return None

    return to_correct_value_type(properties[0])


def extract_properties(ref_obj):
    """Extract properties into a dictionary"""
    if ref_obj is None or not isinstance(ref_obj, dict):
        return {}

    properties = ref_obj.get("properties", [])
    return {prop["label"]: to_correct_value_type(prop) for prop in properties}


def extract_all_properties(ref_column):
    """Extract all properties of each row"""
    properties_df = ref_column.apply(extract_properties).apply(pd.Series)
    return properties_df


def add_property_columns(df, ref_obj_column_name="referenceObject") -> pd.DataFrame:
    """Extract all occuring property values and add as columns to dataframe

    Only adds properties having a value actually present in at least one row's referenceObject.
    Other rows having no value will get null as such a property's value.

    If you want to ensure that an actual property column is there at the end, even
    if this property never occurs, you must attach it explicitely.


    Result is a new dataframe.
    """
    properties_df = extract_all_properties(df[ref_obj_column_name])
    result = pd.concat([df, properties_df], axis=1)
    return result


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


# %%
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "asset_node_id": {"data_type": "STRING", "default_value": None},
        "starts_with": {"data_type": "STRING", "default_value": None},
        "recursive": {"data_type": "BOOLEAN", "default_value": True},
        "attach_properties": {"data_type": "ANY", "default_value": None},
        "attach_all_properties": {"data_type": "BOOLEAN", "default_value": True},
        "drop_ref_obj_column": {"data_type": "BOOLEAN", "default_value": True},
        "name_regexp": {"data_type": "STRING", "default_value": None},
    },
    "outputs": {
        "assets": {"data_type": "DATAFRAME"},
    },
    "name": "Hetida Platform Assets",
    "category": "hetida platform Sources",
    "description": "Load asset data from hetida platform",
    "version_tag": "0.1.5",
    "id": "73f4078c-7672-471a-b852-98a35df7bb3b",
    "revision_group_id": "654c7e54-066a-4631-812b-21609cf5ae2c",
    "state": "RELEASED",
    "released_timestamp": "2026-01-08T15:56:42.013272+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


async def main(
    *,
    asset_node_id=None,
    starts_with=None,
    recursive=True,
    attach_properties=parse_default_value(COMPONENT_INFO, "attach_properties"),
    attach_all_properties=True,
    drop_ref_obj_column=True,
    name_regexp=None,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    asset_node_id = ensure_asset_node_id(asset_node_id)

    children_url = posix_urljoin(PLATFORM_API_URL, "nodes", asset_node_id, "children")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            children_url,
            headers=await get_external_auth_headers(),
            params={"recursive": recursive},
        )

    if resp.status_code != 200:
        msg = f"Request getting asset node children failed with status code: {resp.status_code}"
        logger.error(msg)
        resp.raise_for_status()

    all_children = resp.json()

    asset_children = [child for child in all_children if child["nodeType"] == "ASSET"]

    selected_children = [
        child
        for child in asset_children
        if child["name"].lower().startswith(starts_with.lower() if starts_with else "")
    ]

    # Filter by name_regexp
    if name_regexp:
        selected_children = [
            child
            for child in selected_children
            if (re.fullmatch(name_regexp, child["name"]) is not None)
        ]

    assets_df = pd.DataFrame(selected_children)

    # add assetType name as column:
    assets_df["assetType.name"] = assets_df["referenceObject"].apply(
        lambda x: x["assetType"]["name"]
    )

    if attach_all_properties:
        assets_df = add_property_columns(assets_df)

    if attach_properties is not None:
        for property_name in attach_properties:
            assets_df[property_name] = assets_df["referenceObject"].apply(
                lambda x: extract_property_value(x, property_name)  # noqa: B023
            )
    if drop_ref_obj_column:
        assets_df = assets_df.drop("referenceObject", axis=1)

    return {"assets": assets_df}


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "asset_node_id",
            "filters": {"value": "3cbf482e-990f-4e39-8b8c-95c25a1333cd"},
        },
        {
            "workflow_input_name": "starts_with",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "recursive",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
        {
            "workflow_input_name": "attach_properties",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "attach_all_properties",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "drop_ref_obj_column",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "name_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
    ]
}
RELEASE_WIRING = {
    "input_wirings": [
        {
            "workflow_input_name": "asset_node_id",
            "filters": {"value": "3cbf482e-990f-4e39-8b8c-95c25a1333cd"},
        },
        {
            "workflow_input_name": "starts_with",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "recursive",
            "use_default_value": True,
            "filters": {"value": "True"},
        },
        {
            "workflow_input_name": "attach_properties",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
        {
            "workflow_input_name": "attach_all_properties",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "drop_ref_obj_column",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
        {
            "workflow_input_name": "name_regexp",
            "use_default_value": True,
            "filters": {"value": "null"},
        },
    ]
}


# %%
