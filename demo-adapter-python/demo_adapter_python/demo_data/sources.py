from typing import Any, Dict, List, Optional

from demo_adapter_python.external_types import ExternalType

# pylint: disable=duplicate-code

sources_json_objects: List[Dict[str, Any]] = [
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantA.plant_temperature_unit",
        "thingNodeId": "root.plantA",
        "name": "Temperature Unit",
        "path": "Plant A",
        "metadataKey": "Temperature Unit",
        "type": ExternalType.METADATA_STR,
    },
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantA.plant_pressure_unit",
        "thingNodeId": "root.plantA",
        "name": "Pressure Unit",
        "path": "Plant A",
        "metadataKey": "Pressure Unit",
        "type": ExternalType.METADATA_STR,
    },
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantB.plant_temperature_unit",
        "thingNodeId": "root.plantB",
        "name": "Temperature Unit",
        "path": "Plant B",
        "metadataKey": "Temperature Unit",
        "type": ExternalType.METADATA_STR,
    },
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantB.plant_pressure_unit",
        "thingNodeId": "root.plantB",
        "name": "Pressure Unit",
        "path": "Plant B",
        "metadataKey": "Pressure Unit",
        "type": ExternalType.METADATA_STR,
    },
    {
        "id": "root.plantA.masterdata",
        "thingNodeId": "root.plantA",
        "name": "Masterdata",
        "path": "Plant A",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantB.masterdata",
        "thingNodeId": "root.plantB",
        "name": "Masterdata",
        "path": "Plant B",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantA.alerts",
        "thingNodeId": "root.plantA",
        "name": "Alerts",
        "path": "Plant A",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantB.alerts",
        "thingNodeId": "root.plantB",
        "name": "Alerts",
        "path": "Plant B",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantA.maintenance_events",
        "thingNodeId": "root.plantA",
        "name": "Maintenance Events",
        "path": "Plant A",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantB.maintenance_events",
        "thingNodeId": "root.plantB",
        "name": "Maintenance Events",
        "path": "Plant B",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantA.picklingUnit.influx.temp",
        "thingNodeId": "root.plantA.picklingUnit.influx",
        "name": "Influx Temperature",
        "path": "Plant A / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.picklingUnit.influx.press",
        "thingNodeId": "root.plantA.picklingUnit.influx",
        "name": "Influx Pressure",
        "path": "Plant A / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.influx.temp",
        "thingNodeId": "root.plantA.millingUnit.influx",
        "name": "Influx Temperature",
        "path": "Plant A / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.influx.press",
        "thingNodeId": "root.plantA.millingUnit.influx",
        "name": "Influx Pressure",
        "path": "Plant A / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.picklingUnit.outfeed.temp",
        "thingNodeId": "root.plantA.picklingUnit.outfeed",
        "name": "Outfeed Temperature",
        "path": "Plant A / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.picklingUnit.outfeed.press",
        "thingNodeId": "root.plantA.picklingUnit.outfeed",
        "name": "Outfeed Pressure",
        "path": "Plant A / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.outfeed.temp",
        "thingNodeId": "root.plantA.millingUnit.outfeed",
        "name": "Outfeed Temperature",
        "path": "Plant A / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.outfeed.press",
        "thingNodeId": "root.plantA.millingUnit.outfeed",
        "name": "Outfeed Pressure",
        "path": "Plant A / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.influx.temp",
        "thingNodeId": "root/plantB/picklingUnit/influx",
        "name": "Influx Temperature",
        "path": "Plant B / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.influx.press",
        "thingNodeId": "root.plantB.picklingUnit.influx",
        "name": "Influx Pressure",
        "path": "Plant B / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.influx.temp",
        "thingNodeId": "root.plantB.millingUnit.influx",
        "name": "Influx Temperature",
        "path": "Plant B / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.influx.press",
        "thingNodeId": "root.plantB.millingUnit.influx",
        "name": "Influx Pressure",
        "path": "Plant B / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.outfeed.temp",
        "thingNodeId": "root.plantB.picklingUnit.outfeed",
        "name": "Outfeed Temperature",
        "path": "Plant B / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.outfeed.press",
        "thingNodeId": "root.plantB.picklingUnit.outfeed",
        "name": "Outfeed Pressure",
        "path": "Plant B / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.outfeed.temp",
        "thingNodeId": "root.plantB.millingUnit.outfeed",
        "name": "Outfeed Temperature",
        "path": "Plant B / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.outfeed.press",
        "thingNodeId": "root.plantB.millingUnit.outfeed",
        "name": "Outfeed Pressure",
        "path": "Plant B / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.picklingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantA.picklingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant A / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantA.millingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant A / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.picklingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantA.picklingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant A / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantA.millingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantA.millingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant A / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantB.picklingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant B / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantB.millingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant B / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.picklingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantB.picklingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant B / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
    {
        "id": "root.plantB.millingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantB.millingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant B / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
    },
]


def get_sources(
    parent_id: Optional[str] = None,
    filter_str: Optional[str] = None,
    include_sub_objects: bool = False,
) -> List[Dict[str, Any]]:
    if parent_id is None:
        if include_sub_objects:
            selected_sources = sources_json_objects
        else:
            selected_sources = []
    else:
        if include_sub_objects:
            selected_sources = [
                src
                for src in sources_json_objects
                if src["id"].startswith(parent_id)
                and len(src["id"]) != len(parent_id)  # only true subnodes!
            ]
        else:
            selected_sources = [
                src for src in sources_json_objects if src["thingNodeId"] == parent_id
            ]

    if filter_str is not None:
        selected_sources = [
            src
            for src in selected_sources
            if ((filter_str.lower() in (src["path"] + src["name"]).lower()))
        ]

    return selected_sources
