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
* "drop_ref_obj_column": {"data_type": "BOOLEAN", "default_value": True}: Whether the ref object column (from which properties are collected) and the inherited properties column should be excluded from the final dataframe.
* "name_regexp": {"data_type": "STRING", "default_value": None}: If set, filter for assets with name matching the provided regexp.
* "resolve_inherited_properties": {"data_type": "BOOLEAN", "default_value": True}: Whether property values an asset inherits from its ancestors in the hierarchy are used for assets not setting the respective property themselves.


## Outputs
* "assets": {"data_type": "DATAFRAME"}: Dataframe with one asset per row with columns like "name", "id", "assetType.name", "parentId", "parentName" and more with addtional columns for the properties if requested.

## Details
* The node columns ("id", "name", "parentId", "description", ..., "assetType.name") are always present, even if no asset is selected at all. In that case the result has no rows.
* Does not include the asset note from asset_node_id, i.e. the overall parent, only children (recursively, if requested).
* If you want to ensure that a property column is there you cannot rely on automatic property addition (`attach_all_properties`): If property never occurs, it will not be added as column. Instead you have to explicitely request the property by setting e.g `attach_properties` to something like `["my_property"]`.
* Property values are the effective values: An asset's own value if it has one. Otherwise, if `resolve_inherited_properties` is true, the value it inherits from its nearest ancestor carrying a value. In hetida platform a property without value (null or empty string) means "inherit" and does not blank the property. If no value can be found, the property value is null.
* Inherited values require a hetida platform version providing inherited properties on the node children endpoint (`withInheritedProperties` query parameter). Older platform versions ignore this parameter, then only the assets' own values are available.
* Property columns never replace or duplicate the columns of the nodes themselves ("id", "name", "description", "icon", "assetType.name", ...): If a property has the name of such a column, its column is named with the prefix "property." instead, e.g. "property.description", and a warning is logged. This applies to `attach_all_properties` as well as to `attach_properties`. The mapping from property name to column name for all attached properties is available in the `attrs` of the resulting dataframe under the key "property_columns".
* The origin of inherited values is available as metadata in the `attrs` of the resulting dataframe under the key "inherited_properties": A mapping from asset node id to a mapping from property name to `{"inheritedFromNodeId": ..., "inheritedFromName": ...}`. It only contains properties whose value actually is inherited.

## Examples

Output may e.g. look like (hetida designer dataframe json):

```
{
  "__hd_wrapped_data_object__": "DATAFRAME",
  "__metadata__": {
    "property_columns": {
      "capacity": "capacity",
      "latitude": "latitude",
      "longitude": "longitude"
    },
    "inherited_properties": {
      "206c829a-d591-4c09-978b-84581ee33fe1": {
        "capacity": {
          "inheritedFromNodeId": "3cbf482e-990f-4e39-8b8c-95c25a1333cd",
          "inheritedFromName": "Main Area"
        }
      }
    }
  },
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
from uuid import UUID

import httpx
import pandas as pd

from hdutils import ComponentInputValidationException
from hetdesrun.runtime.context import get_hierarchy_object_info
from hetdesrun.webservice.auth_dependency import get_auth_headers

logger = logging.getLogger(__name__)


# Columns stemming from the nodes (NodeDto) of the hetida platform node children endpoint, in
# the order the platform delivers them. Used for the columns of an empty result. Property columns
# must not replace or duplicate them. Columns actually occurring in the node data are considered,
# too, in case the platform adds fields.
NODE_COLUMNS = (
    "id",
    "parentId",
    "parentName",
    "referenceId",
    "name",
    "nodeType",
    "icon",
    "description",
    "hasChildren",
    "parentIdPath",
    "parentNamePath",
    "isEditable",
    "isDeletable",
    "onlyUsedToShowChildElement",
    "referenceObject",
    "inheritedProperties",
)
PROPERTY_COLUMN_PREFIX = "property."


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


async def fetch_node_children(platform_api_url: str, asset_node_id: str, params: dict) -> list:
    """Obtain the children of a node from the hetida platform node children endpoint"""
    children_url = posix_urljoin(platform_api_url, "nodes", asset_node_id, "children")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            children_url,
            headers=await get_external_auth_headers(),
            params=params,
        )

    if resp.status_code != 200:
        msg = f"Request getting asset node children failed with status code: {resp.status_code}"
        logger.error(msg)
        resp.raise_for_status()

    return resp.json()


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


def convert_property_value(prop, child, inherited: bool):
    """Convert property value according to its type with a helpful error message

    Raises ValueError naming the asset, the property and the origin of the value if
    the value cannot be converted.
    """
    try:
        return to_correct_value_type(prop)
    except (ValueError, TypeError) as e:
        origin = (
            f", inherited from '{prop.get('inheritedFromName')}'"
            f" (node id {prop.get('inheritedFromNodeId')})"
            if inherited
            else ""
        )
        raise ValueError(
            f"Cannot convert value {prop.get('value')!r} of property '{prop.get('label')}'"
            f" (type {prop.get('type')}) of asset '{child.get('name')}'"
            f" (node id {child.get('id')}){origin}: {e}"
        ) from e


def extract_asset_type_name(child):
    """Extract the asset type name from an asset node

    Returns None if not available, e.g. if the referenceObject was removed by hetida platform
    because the node is only visible to reveal accessible children.
    """
    ref_obj = child.get("referenceObject")
    if not isinstance(ref_obj, dict) or not isinstance(ref_obj.get("assetType"), dict):
        return None
    return ref_obj["assetType"].get("name")


def extract_effective_properties(child, resolve_inherited: bool) -> tuple[dict, dict]:
    """Extract effective property values of an asset node

    The asset's own value wins. For properties without own value the inherited value
    is used if resolve_inherited is True. Inherited values are resolved by hetida platform
    and are only present in the node if the platform supports this.

    Returns a pair of dictionaries: property name to value (None if there is no value)
    and property name to origin for those values that are actually inherited.
    """
    ref_obj = child.get("referenceObject")
    own_properties = (ref_obj.get("properties") or []) if isinstance(ref_obj, dict) else []

    values = {}
    for prop in own_properties:
        label = prop.get("label")
        if label is None:
            continue
        if values.get(label) is None:
            values[label] = convert_property_value(prop, child, inherited=False)

    origins = {}
    if resolve_inherited:
        for inherited_prop in child.get("inheritedProperties") or []:
            label = inherited_prop.get("label")
            if label is None or values.get(label) is not None:
                continue
            values[label] = convert_property_value(inherited_prop, child, inherited=True)
            if values[label] is not None:
                origins[label] = {
                    "inheritedFromNodeId": inherited_prop.get("inheritedFromNodeId"),
                    "inheritedFromName": inherited_prop.get("inheritedFromName"),
                }

    return values, origins


def determine_property_columns(property_names, node_columns) -> dict[str, str]:
    """Map property names to column names avoiding collisions with node columns

    Properties having the name of a node column get a column name with PROPERTY_COLUMN_PREFIX.
    """
    property_columns = {
        name: (PROPERTY_COLUMN_PREFIX + name if name in node_columns else name)
        for name in property_names
    }

    renamed = {name: column for name, column in property_columns.items() if name != column}
    if len(renamed) > 0:
        logger.warning(
            "Properties having the name of a node column are attached with prefixed"
            " column names: %s",
            renamed,
        )

    colliding_columns = sorted(column for column in renamed.values() if column in property_columns)
    if len(colliding_columns) > 0:
        raise ValueError(
            f"Cannot attach properties: The column names {colliding_columns} for properties"
            " colliding with node columns are property names themselves."
        )

    return property_columns


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
        "resolve_inherited_properties": {"data_type": "BOOLEAN", "default_value": True},
    },
    "outputs": {
        "assets": {"data_type": "DATAFRAME"},
    },
    "name": "Hetida Platform Assets",
    "category": "hetida platform Sources",
    "description": "Load asset data from hetida platform",
    "version_tag": "0.1.6",
    "id": "16fb6548-f620-4c76-9e7a-e2c1f72ca300",
    "revision_group_id": "654c7e54-066a-4631-812b-21609cf5ae2c",
    "state": "RELEASED",
    "released_timestamp": "2026-09-24T20:28:40.589422+00:00",
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
    resolve_inherited_properties=True,
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****

    platform_api_url = get_platform_api_url()

    asset_node_id = ensure_asset_node_id(asset_node_id)

    all_children = await fetch_node_children(
        platform_api_url,
        asset_node_id,
        params={
            "recursive": recursive,
            "withInheritedProperties": resolve_inherited_properties,
        },
    )

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

    effective_properties = [
        extract_effective_properties(child, resolve_inherited_properties)
        for child in selected_children
    ]
    property_values = [values for values, _ in effective_properties]

    # Without selected children there are no node dicts to take columns from:
    assets_df = (
        pd.DataFrame(selected_children)
        if len(selected_children) > 0
        else pd.DataFrame(columns=list(NODE_COLUMNS))
    )

    # add assetType name as column:
    assets_df["assetType.name"] = [extract_asset_type_name(child) for child in selected_children]

    # properties to attach, in order of first occurrence:
    property_names = list(
        dict.fromkeys(
            [name for values in property_values for name in values] if attach_all_properties else []
        )
    )
    if attach_properties is not None:
        property_names += [name for name in attach_properties if name not in property_names]

    property_columns = determine_property_columns(
        property_names, node_columns=set(NODE_COLUMNS) | set(assets_df.columns)
    )

    assets_df = pd.concat(
        [
            assets_df,
            pd.DataFrame(
                {
                    column: [values.get(name) for values in property_values]
                    for name, column in property_columns.items()
                },
                index=assets_df.index,
            ),
        ],
        axis=1,
    )

    if drop_ref_obj_column:
        assets_df = assets_df.drop(
            columns=["referenceObject", "inheritedProperties"], errors="ignore"
        )

    assets_df.attrs = {
        "property_columns": property_columns,
        "inherited_properties": {
            child["id"]: origins
            for child, (_, origins) in zip(selected_children, effective_properties, strict=True)
            if len(origins) > 0
        },
    }

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
        {
            "workflow_input_name": "resolve_inherited_properties",
            "use_default_value": True,
            "filters": {"value": "true"},
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
        {
            "workflow_input_name": "resolve_inherited_properties",
            "use_default_value": True,
            "filters": {"value": "true"},
        },
    ]
}


# %%
