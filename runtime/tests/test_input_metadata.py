import logging
from contextlib import nullcontext
from copy import deepcopy
from typing import Any
from unittest import mock

import pandas as pd
import pytest
from hdhelpers.metadata import META_KEY, attach_metadata, read_metadata

from hdutils import DataType
from hetdesrun.adapters.exceptions import AdapterInputDataError
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.runtime.input_metadata import attach_input_metadata
from hetdesrun.webservice.config import MetadataValidationMode, RuntimeConfig

ADAPTER_KEY = "demo-adapter-python"


def series_metadata(ts_id: str, **metric_fields: Any) -> dict[str, Any]:
    return {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": ts_id,
            "queried_metrics": [ts_id],
            "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
            "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": ts_id,
                "name": f"name of {ts_id}",
                "value_dimensions": [{"column": "value", "unit": "m", "measurement": None}],
            }
            | metric_fields
        ],
    }


valid_series_metadata = series_metadata("ts_1")
# an error (metrics as mapping) and a warning (unit not under value_dimensions) respectively
invalid_series_metadata = {"metrics": {"ts_2": {"unit": "m"}}}
series_metadata_with_warning = series_metadata("ts_3", unit="m")


def series(attrs: dict[str, Any]) -> pd.Series:
    ser = pd.Series([1.0, 2.0], index=pd.date_range("2026-10-18T06:00:00Z", periods=2, freq="1h"))
    ser.attrs = deepcopy(attrs)
    return ser


def multitsframe(attrs: dict[str, Any], metrics: list[str]) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-18T06:00:00Z", periods=len(metrics), freq="1h"),
            "metric": metrics,
            "value": [float(index) for index in range(len(metrics))],
        }
    )
    frame.attrs = deepcopy(attrs)
    return frame


def wiring(*input_names: str, adapter_id: str | int = ADAPTER_KEY, **kwargs: Any) -> WorkflowWiring:
    return WorkflowWiring(
        input_wirings=[
            InputWiring(
                workflow_input_name=input_name,
                adapter_id=adapter_id,
                ref_id=f"source of {input_name}",
                **kwargs,
            )
            for input_name in input_names
        ]
    )


@pytest.fixture
def validation_mode(request: pytest.FixtureRequest) -> Any:
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.adapter_metadata_validation",
        {ADAPTER_KEY: request.param},
    ):
        yield request.param


def test_conforming_metadata_is_attached_as_model(caplog: pytest.LogCaptureFixture) -> None:
    ser = series(valid_series_metadata | {"other": 1})

    with caplog.at_level(logging.WARNING):
        attach_input_metadata({"inp": ser}, wiring("inp"), {"inp": DataType.Series})

    assert set(ser.attrs) == {META_KEY, "other"}
    meta = read_metadata(ser, "SERIES", required=True)
    assert meta.unit() == "m"
    assert caplog.text == ""


@pytest.mark.parametrize(
    ("adapter_id", "validation_mode"),
    [
        (ADAPTER_KEY, MetadataValidationMode.OFF),
        # OFF is the default for adapters not configured
        ("unconfigured-adapter", MetadataValidationMode.ERROR),
    ],
    indirect=["validation_mode"],
)
def test_off_does_not_check(
    adapter_id: str, validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    valid, invalid, without = (
        series(valid_series_metadata),
        series(invalid_series_metadata),
        series({}),
    )

    with caplog.at_level(logging.WARNING):
        attach_input_metadata(
            {"valid": valid, "invalid": invalid, "without": without},
            wiring("valid", "invalid", "without", adapter_id=adapter_id),
            dict.fromkeys(["valid", "invalid", "without"], DataType.Series),
        )

    assert caplog.text == ""
    # attached nevertheless if valid
    assert META_KEY in valid.attrs
    assert invalid.attrs == invalid_series_metadata
    assert without.attrs == {}


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.WARN], indirect=True)
def test_warn_logs_issues(validation_mode: Any, caplog: pytest.LogCaptureFixture) -> None:
    objs = {
        "inp_1": series(valid_series_metadata),
        "inp_2": series(invalid_series_metadata),
        "inp_3": series(series_metadata_with_warning),
    }

    with caplog.at_level(logging.WARNING):
        attach_input_metadata(objs, wiring(*objs), dict.fromkeys(objs, "SERIES"))

    # one warning summarizing the issues of all inputs of the adapter
    warnings = [record.getMessage() for record in caplog.records]
    assert len(warnings) == 1
    assert (
        f"adapter {ADAPTER_KEY} for workflow inputs inp_2 (source source of inp_2),"
        " inp_3 (source source of inp_3)"
    ) in warnings[0]
    assert "* error at metrics: Input should be a valid array." in warnings[0]
    assert "(in inputs inp_2)" in warnings[0]
    assert "* warning at metrics[0].unit:" in warnings[0]
    # metadata with warnings only is attached, invalid metadata stays as it is
    assert META_KEY in objs["inp_3"].attrs
    assert objs["inp_2"].attrs == invalid_series_metadata


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_error_raises_for_errors_and_logs_warnings(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    objs = {
        "inp_1": series(valid_series_metadata),
        "inp_2": series(invalid_series_metadata),
        "inp_3": series(series_metadata_with_warning),
    }

    with caplog.at_level(logging.WARNING), pytest.raises(AdapterInputDataError) as exc_info:
        attach_input_metadata(objs, wiring(*objs), dict.fromkeys(objs, "SERIES"))

    assert f"adapter {ADAPTER_KEY} for workflow input inp_2 (source source of inp_2)" in str(
        exc_info.value
    )
    assert "inp_3" not in str(exc_info.value)
    assert [record.levelno for record in caplog.records] == [logging.WARNING]
    assert "workflow input inp_3" in caplog.records[0].getMessage()
    # nothing is attached
    assert all(META_KEY not in obj.attrs for obj in objs.values())


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_metadata_is_checked_against_the_data(validation_mode: Any) -> None:
    attrs = {
        "dataset_metadata": series_metadata("a")["dataset_metadata"]
        | {"single_metric": None, "queried_metrics": ["a"]},
        "metrics": series_metadata("a")["metrics"],
    }
    frame = multitsframe(attrs, ["a", "b"])

    with pytest.raises(AdapterInputDataError, match="metrics"):
        attach_input_metadata({"inp": frame}, wiring("inp"), {"inp": DataType.MultiTSFrame})


@pytest.mark.parametrize(
    "validation_mode", [MetadataValidationMode.WARN, MetadataValidationMode.ERROR], indirect=True
)
def test_inputs_without_metadata_are_checked(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    ser = series({"some": "attrs"})

    with (
        caplog.at_level(logging.WARNING),
        pytest.raises(AdapterInputDataError)
        if validation_mode == MetadataValidationMode.ERROR
        else nullcontext() as exc_info,
    ):
        attach_input_metadata({"inp": ser}, wiring("inp"), {"inp": DataType.Series})

    message = str(exc_info.value) if exc_info is not None else caplog.records[0].getMessage()
    assert "* error at dataset_metadata: Field required" in message
    assert "* error at metrics: Field required" in message
    # other top-level keys of attrs are no unknown fields
    assert "some" not in message
    assert ser.attrs == {"some": "attrs"}


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_other_inputs_are_skipped(validation_mode: Any) -> None:
    dataframe = pd.DataFrame({"a": [1.0]})
    dataframe.attrs = deepcopy(invalid_series_metadata)
    any_series = series(invalid_series_metadata)
    default_series = series(invalid_series_metadata)

    attach_input_metadata(
        {"dataframe": dataframe, "any": any_series, "default": default_series, "none": None},
        WorkflowWiring(
            input_wirings=wiring("dataframe", "any", "none").input_wirings
            + wiring("default", use_default_value=True).input_wirings
        ),
        {
            "dataframe": DataType.DataFrame,
            "any": DataType.Any,
            "default": DataType.Series,
            "none": DataType.Series,
        },
    )


def test_adapter_id_1_is_direct_provisioning() -> None:
    with (
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.adapter_metadata_validation",
            {"direct_provisioning": MetadataValidationMode.ERROR},
        ),
        pytest.raises(AdapterInputDataError, match="adapter direct_provisioning for workflow"),
    ):
        attach_input_metadata(
            {"inp": series(invalid_series_metadata)},
            wiring("inp", adapter_id=1),
            {"inp": DataType.Series},
        )


def test_attached_model_is_kept(caplog: pytest.LogCaptureFixture) -> None:
    ser = series(valid_series_metadata)
    meta = attach_metadata(ser)

    with caplog.at_level(logging.WARNING):
        attach_input_metadata({"inp": ser}, wiring("inp"), {"inp": DataType.Series})

    assert ser.attrs[META_KEY] is meta
    assert caplog.text == ""


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.WARN], indirect=True)
def test_issues_of_many_inputs_and_metrics_are_summarized(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    ts_ids = [f"ts_{index}" for index in range(100)]
    # the same unknown field in every metric of every input
    objs: dict[str, pd.Series | pd.DataFrame] = {
        ts_id: series(series_metadata(ts_id, externalId=ts_id)) for ts_id in ts_ids
    }
    frame = multitsframe(
        {
            "dataset_metadata": series_metadata("a")["dataset_metadata"]
            | {"single_metric": None, "queried_metrics": ts_ids},
            "metrics": [series_metadata(ts_id, externalId=ts_id)["metrics"][0] for ts_id in ts_ids],
        },
        [],
    )

    with caplog.at_level(logging.WARNING):
        attach_input_metadata(objs, wiring(*ts_ids), dict.fromkeys(ts_ids, "SERIES"))
        attach_input_metadata({"frame": frame}, wiring("frame"), {"frame": "MULTITSFRAME"})

    issue = 'Unknown field "externalId". Did you mean "external_id"?'
    series_warning, multitsframe_warning = (record.getMessage() for record in caplog.records)
    inputs = "ts_0, ts_1, ts_2, ts_3, ts_4 and 95 more"
    assert series_warning.splitlines()[1:] == [
        f"* warning at metrics[0].externalId: {issue} (in inputs {inputs})"
    ]
    assert multitsframe_warning.splitlines()[1:] == [
        f"* warning at metrics[*].externalId: {issue} (100 times)"
    ]


def test_validation_mode_configuration_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "ADAPTER_METADATA_VALIDATION",
        '{"hetida-platform-adapter": "OFF", "demo-adapter-python": "ERROR"}',
    )

    assert RuntimeConfig().adapter_metadata_validation == {
        "hetida-platform-adapter": MetadataValidationMode.OFF,
        "demo-adapter-python": MetadataValidationMode.ERROR,
    }
