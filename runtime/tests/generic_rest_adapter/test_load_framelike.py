import io
import warnings

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.load_framelike import parse_framelike_response_stream

# ISO-8601 timestamps of differing precision as Java's ISO_INSTANT (the Jackson default for Instant)
# writes them, omitting the fraction of whole seconds, plus one with an UTC offset
MIXED_PRECISION_TIMESTAMPS = [
    "2026-10-26T16:46:27Z",
    "2026-10-26T16:46:27.123Z",
    "2026-10-26T16:46:28Z",
    "2026-10-26T16:46:28.123456Z",
    "2026-10-26T16:46:29.123456789Z",
    "2026-10-26T17:46:30.5+01:00",
]
EXPECTED_UTC_TIMESTAMPS = pd.DatetimeIndex(
    [
        "2026-10-26T16:46:27Z",
        "2026-10-26T16:46:27.123Z",
        "2026-10-26T16:46:28Z",
        "2026-10-26T16:46:28.123456Z",
        "2026-10-26T16:46:29.123456789Z",
        "2026-10-26T16:46:30.5Z",
    ]
).as_unit("ns")
TIMESERIES_ENDPOINTS = ["timeseries", "multitsframe", "singletsframe"]


def ndjson(timestamps: list[str], value_key: str = "value") -> io.BytesIO:
    return io.BytesIO(
        b"".join(
            b'{"timeseriesId": "1", "timestamp": "%s", "%s": %d}\n'
            % (timestamp.encode(), value_key.encode(), i)
            for i, timestamp in enumerate(timestamps)
        )
    )


@pytest.mark.parametrize("endpoint", TIMESERIES_ENDPOINTS)
@pytest.mark.parametrize("reverse", [False, True], ids=["whole_seconds_first", "fraction_first"])
def test_parse_timeseries_timestamps_of_differing_precision(endpoint: str, reverse: bool) -> None:
    timestamps = MIXED_PRECISION_TIMESTAMPS[::-1] if reverse else MIXED_PRECISION_TIMESTAMPS
    expected = EXPECTED_UTC_TIMESTAMPS[::-1] if reverse else EXPECTED_UTC_TIMESTAMPS

    df = parse_framelike_response_stream(ndjson(timestamps), endpoint)

    assert df["timestamp"].dtype == "datetime64[ns, UTC]"
    assert pd.DatetimeIndex(df["timestamp"]).equals(expected)


def test_parse_timeseries_timestamps_of_whole_seconds_only() -> None:
    # without schema pyarrow would parse these itself, as unit s
    df = parse_framelike_response_stream(
        ndjson(["2026-10-26T16:46:27Z", "2026-10-26T17:46:28+01:00"]), "timeseries"
    )

    assert df["timestamp"].dtype == "datetime64[us, UTC]"
    assert pd.DatetimeIndex(df["timestamp"]).equals(
        pd.DatetimeIndex(["2026-10-26T16:46:27Z", "2026-10-26T16:46:28Z"])
    )


@pytest.mark.parametrize(
    ("fraction", "unit"),
    [(".123", "us"), (".123456", "us"), (".123000000", "us"), (".123456789", "ns")],
)
def test_parse_timeseries_timestamps_as_us_unless_sub_microsecond(fraction: str, unit: str) -> None:
    df = parse_framelike_response_stream(
        ndjson(["2026-10-26T16:46:27Z", f"2026-10-26T16:46:28{fraction}Z"]), "timeseries"
    )

    assert df["timestamp"].dtype == f"datetime64[{unit}, UTC]"
    assert df["timestamp"].iloc[1] == pd.Timestamp(f"2026-10-26T16:46:28{fraction}Z")


def test_parse_timeseries_timestamps_without_offset_as_utc() -> None:
    df = parse_framelike_response_stream(
        ndjson(["2026-10-26T16:46:27", "2026-10-26 16:46:28.5", "2026-10-27"]), "timeseries"
    )

    assert pd.DatetimeIndex(df["timestamp"]).equals(
        pd.DatetimeIndex(["2026-10-26T16:46:27Z", "2026-10-26T16:46:28.5Z", "2026-10-27T00:00:00Z"])
    )


def test_parse_timeseries_timestamp_column_comes_first() -> None:
    df = parse_framelike_response_stream(
        io.BytesIO(b'{"metric": "a", "timestamp": "2026-10-26T16:46:27Z", "value": 1, "b": 2}\n'),
        "multitsframe",
    )

    assert df.columns.tolist() == ["timestamp", "metric", "value", "b"]


@pytest.mark.parametrize("endpoint", TIMESERIES_ENDPOINTS)
@pytest.mark.parametrize(
    "record", [b'{"timestamp": null, "value": 1}', b'{"value": 1}'], ids=["null", "missing"]
)
def test_parse_timeseries_without_timestamp_fails(endpoint: str, record: bytes) -> None:
    raw = b'{"timestamp": "2026-10-26T16:46:27Z", "value": 0}\n' + record + b"\n"

    with pytest.raises(AdapterHandlingException, match="1 of 2 records without timestamp"):
        parse_framelike_response_stream(io.BytesIO(raw), endpoint)


@pytest.mark.parametrize(
    "timestamp",
    [
        b'"9999-12-31T23:59:59Z"',  # outside of the nanosecond range
        b'"2026-10-26T16:46:27.1234567891Z"',  # more than nanosecond precision
        b'"2026-10-26T16:46:27z"',
        b'"no timestamp"',
        b'"empty"',  # not taken for an empty response
        b"1792946787000000000",
    ],
)
def test_parse_timeseries_with_unparsable_timestamp_fails(timestamp: bytes) -> None:
    raw = b'{"timestamp": "2026-10-26T16:46:27Z", "value": 0}\n{"timestamp": %s, "value": 1}\n'

    with pytest.raises(AdapterHandlingException, match="Could not parse framelike response data"):
        parse_framelike_response_stream(io.BytesIO(raw % timestamp), "timeseries")


@pytest.mark.parametrize("endpoint", [*TIMESERIES_ENDPOINTS, "dataframe"])
@pytest.mark.parametrize("body", [b"", b"\n", b" \n\n"], ids=["nothing", "newline", "whitespace"])
def test_parse_empty_response(endpoint: str, body: bytes) -> None:
    assert parse_framelike_response_stream(io.BytesIO(body), endpoint).shape == (0, 0)


@pytest.mark.parametrize("endpoint", [*TIMESERIES_ENDPOINTS, "dataframe"])
def test_parse_error_mentioning_empty_is_no_empty_response(endpoint: str) -> None:
    raw = (
        b'{"timestamp": "2026-10-26T16:46:27Z", "isEmpty": 1}\n'
        b'{"timestamp": "2026-10-26T16:46:28Z", "isEmpty": "a"}\n'
    )

    with pytest.raises(AdapterHandlingException, match="isEmpty"):
        parse_framelike_response_stream(io.BytesIO(raw), endpoint)


def test_parse_dataframe_timestamps_of_differing_precision() -> None:
    # without the one with an UTC offset: dataframe timestamps are not converted to UTC, and pandas
    # cannot represent differing offsets
    df = parse_framelike_response_stream(
        ndjson(MIXED_PRECISION_TIMESTAMPS[-2::-1], value_key="a"), "dataframe"
    )

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.equals(EXPECTED_UTC_TIMESTAMPS[:-1])  # sorted by the index
    assert df["a"].tolist() == [4, 3, 2, 1, 0]
    assert "timestamp" in df.columns


def test_parse_dataframe_timestamps_of_other_format() -> None:
    df = parse_framelike_response_stream(
        ndjson(["10/27/2026 16:46:27", "10/26/2026 16:46:27"], value_key="a"), "dataframe"
    )

    assert df.index.equals(pd.DatetimeIndex(["2026-10-26 16:46:27", "2026-10-27 16:46:27"]))


def test_parse_dataframe_numeric_timestamps_as_before() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # parsing numbers with format="ISO8601" is deprecated
        df = parse_framelike_response_stream(
            io.BytesIO(b'{"timestamp": 2, "a": 1}\n{"timestamp": 1, "a": 2}\n'), "dataframe"
        )

    assert df.index.equals(pd.DatetimeIndex([1, 2]))


def test_parse_dataframe_with_unparsable_timestamps_keeps_default_index() -> None:
    df = parse_framelike_response_stream(
        ndjson(["2026-10-26T16:46:27Z", "no timestamp"], value_key="a"), "dataframe"
    )

    assert isinstance(df.index, pd.RangeIndex)
    assert df["timestamp"].tolist() == ["2026-10-26T16:46:27Z", "no timestamp"]
