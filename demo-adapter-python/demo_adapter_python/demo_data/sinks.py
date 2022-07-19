from typing import Any, Dict, List, Optional

from demo_adapter_python.external_types import ExternalType

# pylint: disable=duplicate-code

sinks_json_objects: List[Dict[str, Any]] = [
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantA.anomaly_state",
        "thingNodeId": "root.plantA",
        "name": "Anomaly State",
        "path": "Plant A",
        "metadataKey": "Anomaly State",
        "type": ExternalType.METADATA_BOOLEAN,
    },
    {  # metadatum that appears as its own point in the tree and is filterable
        "id": "root.plantB.anomaly_state",
        "thingNodeId": "root.plantB",
        "name": "Anomaly State",
        "path": "Plant B",
        "metadataKey": "Anomaly State",
        "type": ExternalType.METADATA_BOOLEAN,
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
]


def get_sinks(
    parent_id: Optional[str] = None,
    filter_str: Optional[str] = None,
    include_sub_objects: bool = False,
) -> List[Dict[str, Any]]:
    if parent_id is None:
        if include_sub_objects:
            selected_sinks = sinks_json_objects
        else:
            selected_sinks = []
    else:
        if include_sub_objects:
            selected_sinks = [
                snk
                for snk in sinks_json_objects
                if snk["id"].startswith(parent_id)
                and len(snk["id"]) != len(parent_id)  # only true subnodes!
            ]
        else:
            selected_sinks = [
                snk for snk in sinks_json_objects if snk["thingNodeId"] == parent_id
            ]

    if filter_str is not None:
        selected_sinks = [
            snk
            for snk in selected_sinks
            if ((filter_str.lower() in (snk["path"] + snk["name"]).lower()))
        ]

    return selected_sinks
