from typing import Any

from demo_adapter_python.external_types import ExternalType

sinks_json_objects: list[dict[str, Any]] = [
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
        "filters": {"frequency": {"name": "frequency", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantC.picklingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantC.picklingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant C / Pickling Unit / Influx",
        "type": ExternalType.TIMESERIES_NUMERIC,
        "filters": {"frequency": {"name": "frequency", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantA.millingUnit.influx.anomaly_score",
        "thingNodeId": "root.plantA.millingUnit.influx",
        "name": "Influx Anomaly Score",
        "path": "Plant A / Milling Unit / Influx",
        "type": ExternalType.TIMESERIES_FLOAT,
        "filters": {"frequency": {"name": "frequency", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantA.picklingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantA.picklingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant A / Pickling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
        "filters": {"frequency": {"name": "frequency", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantA.millingUnit.outfeed.anomaly_score",
        "thingNodeId": "root.plantA.millingUnit.outfeed",
        "name": "Outfeed Anomaly Score",
        "path": "Plant A / Milling Unit / Outfeed",
        "type": ExternalType.TIMESERIES_FLOAT,
        "filters": {"frequency": {"name": "frequency", "type": "free_text", "required": False}},
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
        "filters": {"column_names": {"name": "columns", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantB.alerts",
        "thingNodeId": "root.plantB",
        "name": "Alerts",
        "path": "Plant B",
        "type": ExternalType.DATAFRAME,
    },
    {
        "id": "root.plantA.anomalies",
        "thingNodeId": "root.plantA",
        "name": "Anomalies",
        "path": "Plant A",
        "type": ExternalType.MULTITSFRAME,
        "filters": {"metric_names": {"name": "metrics", "type": "free_text", "required": False}},
    },
    {
        "id": "root.plantB.anomalies",
        "thingNodeId": "root.plantB",
        "name": "Anomalies",
        "path": "Plant B",
        "type": ExternalType.MULTITSFRAME,
    },
]


def get_sinks(
    parent_id: str | None = None,
    filter_str: str | None = None,
    include_sub_objects: bool = False,
) -> list[dict[str, Any]]:
    if parent_id is None:
        if include_sub_objects:  # noqa: SIM108
            selected_sinks = sinks_json_objects
        else:
            selected_sinks = []
    elif include_sub_objects:
        selected_sinks = [
            snk
            for snk in sinks_json_objects
            if snk["id"].startswith(parent_id)
            and len(snk["id"]) != len(parent_id)  # only true subnodes!
        ]
    else:
        selected_sinks = [snk for snk in sinks_json_objects if snk["thingNodeId"] == parent_id]

    if filter_str is not None:
        selected_sinks = [
            snk
            for snk in selected_sinks
            if (filter_str.lower() in (snk["path"] + snk["name"]).lower())
        ]

    return selected_sinks
