"""The JSON base components extracting and adding/updating attributes with attached metadata"""

import copy
import json
from typing import Any

import pandas as pd
import pytest
from hdhelpers.metadata import META_KEY, attach_metadata, read_metadata

from hetdesrun.component.load import import_func_from_code_wrapper

CONNECTORS_PATH = "transformations/components/connectors/"

EXTRACT_ATTRIBUTES = {
    "SERIES": "extract-attributes-series_100_9b160d5b-f821-4b7a-b314-b2c94e54c983.json",
    "MULTITSFRAME": (
        "extract-attributes-multitsframe_100_f711106f-3ee1-46a6-a70b-ba12d92fe5be.json"
    ),
    "DATAFRAME": "extract-attributes-dataframe_100_816436b2-f303-48af-857c-6c4d7c7a0f4b.json",
}
ADDUPDATE_ATTRIBUTES = {
    "SERIES": "addupdate-attributes-series_100_635d23be-39b5-4665-ac1e-c8e4a001d06d.json",
    "MULTITSFRAME": (
        "addupdate-attributes-multitsframe_100_dbce1015-833e-4b23-bf72-05beb28d5b90.json"
    ),
    "DATAFRAME": "addupdate-attributes-dataframe_100_5372a8bb-717f-4183-a89b-94b0c8d8693a.json",
}
INPUT_NAMES = {"SERIES": "series", "MULTITSFRAME": "multitsframe", "DATAFRAME": "dataframe"}


def component_main(file_name: str):  # type: ignore[no-untyped-def]
    with open(CONNECTORS_PATH + file_name) as f:
        code = json.load(f)["content"]
    return import_func_from_code_wrapper(code, "main")


def metadata(metric_ids: list[str], single_metric: bool) -> dict[str, Any]:
    return {
        "dataset_metadata": {
            "metric_key": "id",
            "queried_metrics": metric_ids,
            "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
            "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
            "ref_interval_type": "closed",
        }
        | ({"single_metric": metric_ids[0]} if single_metric else {}),
        "metrics": [
            {
                "id": metric_id,
                "name": f"Metric {metric_id}",
                "value_dimensions": [{"column": "value", "unit": "m", "measurement": None}],
            }
            for metric_id in metric_ids
        ],
    }


def data_with_attached_metadata(data_type: str) -> tuple[pd.Series | pd.DataFrame, dict]:
    timestamps = pd.to_datetime(["2026-10-18T06:00:00Z", "2026-10-18T07:00:00Z"], utc=True)
    obj: pd.Series | pd.DataFrame
    if data_type == "SERIES":
        obj = pd.Series([1.0, 2.0], index=timestamps)
        attrs = metadata(["a"], single_metric=True)
    else:
        # a DATAFRAME carries attached metadata e.g. after conversion from a MULTITSFRAME
        obj = pd.DataFrame({"timestamp": timestamps, "metric": ["a", "b"], "value": [1.0, 2.0]})
        attrs = metadata(["a", "b"], single_metric=False)
    obj.attrs = copy.deepcopy(attrs) | {"other": 1}
    assert attach_metadata(obj, "SERIES" if data_type == "SERIES" else "MULTITSFRAME") is not None
    return obj, attrs


@pytest.mark.parametrize("data_type", list(EXTRACT_ATTRIBUTES))
def test_extracted_attributes_contain_the_json_form(data_type: str) -> None:
    obj, attrs = data_with_attached_metadata(data_type)

    attributes = component_main(EXTRACT_ATTRIBUTES[data_type])(**{INPUT_NAMES[data_type]: obj})[
        "attributes"
    ]

    assert attributes == attrs | {"other": 1}
    assert META_KEY in obj.attrs


@pytest.mark.parametrize("data_type", ["SERIES", "MULTITSFRAME"])
def test_updated_metadata_is_attached_again(data_type: str) -> None:
    obj, attrs = data_with_attached_metadata(data_type)
    attrs["metrics"][0]["value_dimensions"][0]["unit"] = "cm"

    result = component_main(ADDUPDATE_ATTRIBUTES[data_type])(
        **{INPUT_NAMES[data_type]: obj, "attributes": {"metrics": attrs["metrics"], "new": 2}}
    )[INPUT_NAMES[data_type]]

    assert set(result.attrs) == {META_KEY, "other", "new"}
    meta = read_metadata(result, data_type, required=True)  # type: ignore[call-overload]
    assert meta.unit("a") == "cm"


@pytest.mark.parametrize("data_type", list(ADDUPDATE_ATTRIBUTES))
def test_attributes_not_following_conventions_are_set_in_the_json_form(data_type: str) -> None:
    obj, attrs = data_with_attached_metadata(data_type)
    # e.g. the invalidation instructions for writing to the sql adapter
    update = {"dataset_metadata": {"invalidate_dataset": True}}

    result = component_main(ADDUPDATE_ATTRIBUTES[data_type])(
        **{INPUT_NAMES[data_type]: obj, "attributes": update}
    )[INPUT_NAMES[data_type]]

    assert result.attrs == attrs | {"other": 1} | update
