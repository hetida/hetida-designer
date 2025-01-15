from collections.abc import MutableMapping
from multiprocessing import Manager
from typing import Any

import pandas as pd

from demo_adapter_python.models import Metadatum

manager = Manager()

store = manager.dict()

for plant in ("plantA", "plantB"):
    for unit in ("picklingUnit", "millingUnit"):
        for position in ("influx", "outfeed"):
            # initialize writable attached metadata
            store[f"root.{plant}.{unit}.{position}.temp|Sensor Config"] = Metadatum(
                key="Sensor Config",
                value={"mode": "prod"},
                dataType="any",
                isSink=True,
            )

            store[f"root.{plant}.{unit}.{position}.anomaly_score|Overshooting Allowed"] = Metadatum(
                key="Overshooting Allowed",
                value=False,
                dataType="boolean",
                isSink=True,
            )

            # initialize writable timeseries
            store[f"root.{plant}.{unit}.{position}.anomaly_score"] = pd.DataFrame()


store[f"root.plantC.picklingUnit.influx.anomaly_score"] = pd.DataFrame()

# initialize leaf metadata sinks
for plant in ("plantA", "plantB"):
    store[f"root.{plant}|Anomaly State"] = Metadatum(
        key="Anomaly State",
        value=False,
        dataType="boolean",
        isSink=True,
    )
    store[f"root.{plant}.alerts"] = pd.DataFrame()
    store[f"root.{plant}.anomalies"] = pd.DataFrame([], columns=["timestamp", "metric", "value"])


def get_store() -> MutableMapping[Any, Any]:
    return store


def get_value_from_store(key: str) -> Any:
    return get_store()[key]


def set_value_in_store(key: str, value: Any) -> None:
    get_store()[key] = value


def get_metadatum_from_store(attached_to_id: str, key: str) -> Metadatum:
    stored_metadatum: Metadatum = store[attached_to_id + "|" + key]
    return stored_metadatum


def set_metadatum_in_store(attached_to_id: str, key: str, new_value: Metadatum) -> None:
    store[attached_to_id + "|" + key] = new_value
