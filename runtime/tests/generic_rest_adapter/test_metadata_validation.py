import io
import logging
from typing import Any
from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterInputDataError
from hetdesrun.adapters.generic_rest.load_multitsframe import (
    load_single_multitsframe_from_adapter,
)
from hetdesrun.adapters.generic_rest.load_ts_data import load_ts_data_from_adapter
from hetdesrun.adapters.generic_rest.metadata_validation import validate_received_metadata
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.webservice.config import MetadataValidationMode, RuntimeConfig

ADAPTER_KEY = "validated-adapter"


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


def timeseries_sources(*ids: str) -> list[FilteredSource]:
    return [FilteredSource(ref_id=ts_id, type="timeseries(float)") for ts_id in ids]


def loaded_timeseries(attrs: dict[str, Any]) -> pd.DataFrame:
    df = pd.DataFrame({"timeseriesId": [], "timestamp": [], "value": []})
    df.attrs = attrs
    return df


@pytest.fixture
def validation_mode(request: pytest.FixtureRequest) -> Any:
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.generic_rest_adapter_metadata_validation",
        {ADAPTER_KEY: request.param},
    ):
        yield request.param


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.OFF], indirect=True)
def test_off_does_not_validate(validation_mode: Any, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        validate_received_metadata(
            loaded_timeseries({"ts_2": invalid_series_metadata}),
            ADAPTER_KEY,
            "timeseries",
            timeseries_sources("ts_2"),
        )

    assert caplog.text == ""


def test_adapters_without_configuration_are_not_validated(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        validate_received_metadata(
            loaded_timeseries({"ts_2": invalid_series_metadata}),
            "unconfigured-adapter",
            "timeseries",
            timeseries_sources("ts_2"),
        )

    assert caplog.text == ""


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.WARN], indirect=True)
def test_warn_logs_issues(validation_mode: Any, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING):
        validate_received_metadata(
            loaded_timeseries(
                {
                    "ts_1": valid_series_metadata,
                    "ts_2": invalid_series_metadata,
                    "ts_3": series_metadata_with_warning,
                }
            ),
            ADAPTER_KEY,
            "timeseries",
            timeseries_sources("ts_1", "ts_2", "ts_3", "ts_4"),
        )

    warnings = [record.getMessage() for record in caplog.records]
    assert len(warnings) == 3
    assert f"generic REST adapter {ADAPTER_KEY} for timeseries source ts_2" in warnings[0]
    assert "* error at metrics: Input should be a valid array" in warnings[0]
    assert "source ts_3" in warnings[1]
    assert "* warning at metrics[0].unit:" in warnings[1]
    # no metadata at all for ts_4
    assert "source ts_4" in warnings[2]
    assert "* error at dataset_metadata: Field required" in warnings[2]


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_error_raises_for_errors_and_logs_warnings(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING), pytest.raises(AdapterInputDataError) as exc_info:
        validate_received_metadata(
            loaded_timeseries(
                {"ts_2": invalid_series_metadata, "ts_3": series_metadata_with_warning}
            ),
            ADAPTER_KEY,
            "timeseries",
            timeseries_sources("ts_2", "ts_3"),
        )

    assert f"generic REST adapter {ADAPTER_KEY} for timeseries source ts_2" in str(exc_info.value)
    assert "ts_3" not in str(exc_info.value)
    assert [record.levelno for record in caplog.records] == [logging.WARNING]
    assert "source ts_3" in caplog.records[0].getMessage()


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_error_does_not_raise_for_warnings_only(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    multitsframe = pd.DataFrame(
        {"timestamp": ["2026-10-18T06:00:00Z"] * 2, "metric": ["a", "b"], "value": [1.0, 2.0]}
    )
    multitsframe.attrs = {
        "dataset_metadata": series_metadata("a")["dataset_metadata"]
        | {"single_metric": None, "queried_metrics": ["a", "b"]},
        "metrics": series_metadata("a")["metrics"] + series_metadata("b", Unit="m")["metrics"],
    }

    with caplog.at_level(logging.WARNING):
        validate_received_metadata(
            multitsframe,
            ADAPTER_KEY,
            "multitsframe",
            [FilteredSource(ref_id="frame", type="multitsframe")],
        )

    assert len(caplog.records) == 1
    assert "multitsframe source frame" in caplog.records[0].getMessage()
    assert "* warning at metrics[1].Unit:" in caplog.records[0].getMessage()


@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
def test_dataframes_are_not_validated(validation_mode: Any) -> None:
    dataframe = pd.DataFrame({"a": [1.0]})
    dataframe.attrs = {"metrics": "no conventions for DATAFRAMEs"}

    validate_received_metadata(
        dataframe, ADAPTER_KEY, "dataframe", [FilteredSource(ref_id="df", type="dataframe")]
    )


def response_mock(records: bytes, attrs: dict[str, Any]) -> mock.Mock:
    return mock.Mock(
        status_code=200,
        headers={"Data-Attributes": encode_attributes(attrs)},
        raw=io.BytesIO(records),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
async def test_loading_fails_for_invalid_metadata(validation_mode: Any) -> None:
    resp_mock = response_mock(
        b'{"timestamp": "2026-10-18T06:00:00Z", "metric": "a", "value": 1.0}\n',
        {"dataset_metadata": {"ref_interval_type": "half_open"}},
    )
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.niquests.Session.get",
            return_value=resp_mock,
        ),
        pytest.raises(AdapterInputDataError, match="dataset_metadata.ref_interval_type"),
    ):
        await load_single_multitsframe_from_adapter(
            FilteredSource(ref_id="frame", type="multitsframe", filters={}),
            adapter_key=ADAPTER_KEY,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.ERROR], indirect=True)
async def test_loading_fails_without_metadata(validation_mode: Any) -> None:
    resp_mock = mock.Mock(
        status_code=200,
        headers={},
        raw=io.BytesIO(b'{"timestamp": "2026-10-18T06:00:00Z", "metric": "a", "value": 1.0}\n'),
    )
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.niquests.Session.get",
            return_value=resp_mock,
        ),
        pytest.raises(AdapterInputDataError, match="dataset_metadata: Field required"),
    ):
        await load_single_multitsframe_from_adapter(
            FilteredSource(ref_id="frame", type="multitsframe", filters={}),
            adapter_key=ADAPTER_KEY,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("validation_mode", [MetadataValidationMode.WARN], indirect=True)
async def test_loading_warns_for_invalid_metadata(
    validation_mode: Any, caplog: pytest.LogCaptureFixture
) -> None:
    resp_mock = response_mock(
        b'{"timeseriesId": "ts_2", "timestamp": "2026-10-18T06:00:00Z", "value": 1.0}\n',
        {"ts_2": invalid_series_metadata},
    )
    with (
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ),
        mock.patch(
            "hetdesrun.adapters.generic_rest.load_framelike.niquests.Session.get",
            return_value=resp_mock,
        ),
        caplog.at_level(logging.WARNING),
    ):
        df = await load_ts_data_from_adapter(
            timeseries_sources("ts_2"), filter_params=[], adapter_key=ADAPTER_KEY
        )

    assert df.attrs == {"ts_2": invalid_series_metadata}
    assert any("timeseries source ts_2" in record.getMessage() for record in caplog.records)


def test_validation_mode_configuration_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "GENERIC_REST_ADAPTER_METADATA_VALIDATION",
        '{"hetida-platform-adapter": "WARN", "demo-adapter-python": "ERROR"}',
    )

    assert RuntimeConfig().generic_rest_adapter_metadata_validation == {
        "hetida-platform-adapter": MetadataValidationMode.WARN,
        "demo-adapter-python": MetadataValidationMode.ERROR,
    }
