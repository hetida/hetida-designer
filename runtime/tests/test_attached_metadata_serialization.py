"""Places serializing attrs use the JSON form of metadata attached as model"""

import pickle
from copy import deepcopy
from pathlib import Path
from typing import Any

import msgspec
import pandas as pd
import pytest
from hdhelpers.metadata import META_KEY, attach_metadata

from hdutils import DataType
from hetdesrun.adapters.generic_rest.load_framelike import decode_attributes
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.adapters.local_file.handlers.parquet import load_parquet, write_parquet
from hetdesrun.adapters.local_file.handlers.pickle_handling import load_pickle, write_pickle
from hetdesrun.models.run import WorkflowExecutionResult
from hetdesrun.service.serialization_helpers import (
    encode_workflow_execution_result,
    handle_workflow_execution_dict_serialisation,
)
from hetdesrun.utils import with_json_attrs

SINGLETSFRAME_METADATA: dict[str, Any] = {
    "dataset_metadata": {
        "metric_key": "id",
        "single_metric": "a",
        "queried_metrics": ["a"],
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
    },
    "metrics": [
        {
            "id": "a",
            "name": "A",
            "value_dimensions": [
                {"column": "value", "unit": "m", "measurement": None},
                {"column": "state", "unit": None, "measurement": None},
            ],
        }
    ],
}


def singletsframe_with_attached_metadata() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-18T06:00:00Z", periods=2, freq="1h"),
            "value": [1.0, 2.0],
            "state": [0, 1],
        }
    )
    frame.attrs = deepcopy(SINGLETSFRAME_METADATA) | {"other": 1}
    assert attach_metadata(frame) is not None
    return frame


def series_with_attached_metadata() -> pd.Series:
    metadata = deepcopy(SINGLETSFRAME_METADATA)
    metadata["metrics"][0]["value_dimensions"] = metadata["metrics"][0]["value_dimensions"][:1]
    series = pd.Series([1.0, 2.0])
    series.attrs = metadata | {"other": 1}
    assert attach_metadata(series) is not None
    return series


def test_execution_results_contain_the_json_form() -> None:
    frame = singletsframe_with_attached_metadata()
    series = series_with_attached_metadata()
    result = WorkflowExecutionResult(
        result="ok",
        output_types_by_output_name={"frame": DataType.SingleTSFrame, "series": DataType.Series},
        output_results_by_output_name={"frame": frame, "series": series},
        job_id="00000000-0000-0000-0000-000000000001",
        tr_id="00000000-0000-0000-0000-000000000002",
        tr_name="t",
        tr_tag="1.0.0",
    )

    # the raw path of the runtime and the pydantic path
    for decoded in (
        msgspec.json.decode(encode_workflow_execution_result(result)),
        msgspec.json.decode(
            msgspec.json.encode(handle_workflow_execution_dict_serialisation(result))
        ),
    ):
        outputs = decoded["output_results_by_output_name"]
        assert outputs["frame"]["__metadata__"] == SINGLETSFRAME_METADATA | {"other": 1}
        assert outputs["series"]["__metadata__"]["metrics"][0]["value_dimensions"] == [
            {"column": "value", "unit": "m", "measurement": None}
        ]
    # the outputs keep their models
    assert META_KEY in frame.attrs
    assert META_KEY in series.attrs


def test_generic_rest_data_attributes_contain_the_json_form() -> None:
    frame = singletsframe_with_attached_metadata()

    assert decode_attributes(encode_attributes(frame.attrs)) == SINGLETSFRAME_METADATA | {
        "other": 1
    }


def test_with_json_attrs() -> None:
    frame = singletsframe_with_attached_metadata()

    copied = with_json_attrs(frame)

    assert copied.attrs == SINGLETSFRAME_METADATA | {"other": 1}
    assert META_KEY in frame.attrs
    pd.testing.assert_frame_equal(copied, frame)
    # objects without attached metadata are returned as they are
    assert with_json_attrs(copied) is copied
    assert with_json_attrs({"a": 1}) == {"a": 1}


@pytest.mark.parametrize("file_name", ["frame.pkl", "frame.parquet"])
def test_local_files_contain_the_json_form(tmp_path: Path, file_name: str) -> None:
    write, load = (
        (write_pickle, load_pickle)
        if file_name.endswith("pkl")
        else (
            write_parquet,
            load_parquet,
        )
    )
    path = str(tmp_path / file_name)

    write(with_json_attrs(singletsframe_with_attached_metadata()), path)

    assert load(path).attrs == SINGLETSFRAME_METADATA | {"other": 1}


def test_pickles_contain_no_hdhelpers_classes() -> None:
    pickled = pickle.dumps(with_json_attrs(singletsframe_with_attached_metadata()))

    assert b"hdhelpers" not in pickled
