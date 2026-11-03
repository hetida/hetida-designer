import io
import warnings

import pandas as pd
import pytest

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
)


def ndjson(timestamps: list[str], value_key: str = "value") -> io.BytesIO:
    return io.BytesIO(
        b"".join(
            b'{"timeseriesId": "1", "timestamp": "%s", "%s": %d}\n'
            % (timestamp.encode(), value_key.encode(), i)
            for i, timestamp in enumerate(timestamps)
        )
    )


@pytest.mark.parametrize("endpoint", ["timeseries", "multitsframe", "singletsframe"])
@pytest.mark.parametrize("reverse", [False, True], ids=["whole_seconds_first", "fraction_first"])
def test_parse_timeseries_timestamps_of_differing_precision(endpoint: str, reverse: bool) -> None:
    timestamps = MIXED_PRECISION_TIMESTAMPS[::-1] if reverse else MIXED_PRECISION_TIMESTAMPS
    expected = EXPECTED_UTC_TIMESTAMPS[::-1] if reverse else EXPECTED_UTC_TIMESTAMPS

    df = parse_framelike_response_stream(ndjson(timestamps), endpoint)

    assert df["timestamp"].dt.tz is not None
    assert str(df["timestamp"].dt.tz) == "UTC"
    assert pd.DatetimeIndex(df["timestamp"]).equals(expected)


def test_parse_timeseries_timestamps_of_whole_seconds_only() -> None:
    # pyarrow already parses these itself (as tz-naive UTC), they still end up tz-aware UTC
    df = parse_framelike_response_stream(
        ndjson(["2026-10-26T16:46:27Z", "2026-10-26T17:46:28+01:00"]), "timeseries"
    )

    assert str(df["timestamp"].dt.tz) == "UTC"
    assert pd.DatetimeIndex(df["timestamp"]).equals(
        pd.DatetimeIndex(["2026-10-26T16:46:27Z", "2026-10-26T16:46:28Z"])
    )


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
