import copy
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from hetdesrun.adapters.sql_adapter import load_data, send_data
from hetdesrun.adapters.sql_adapter.config import get_sql_adapter_config
from hetdesrun.adapters.sql_adapter.structure import (
    get_sink_by_id,
    get_sinks,
    get_source_by_id,
    get_sources,
    get_structure,
)
from hetdesrun.models.data_selection import FilteredSink, FilteredSource


def test_sql_timeseries_table_structure(three_sqlite_dbs_configured):
    """Also test source ignoring behaviour!"""

    structure_results = get_structure()
    assert len(structure_results.thingNodes) == 3
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 0

    # ts db
    structure_results = get_structure("read_only_timeseries_sqlite_database")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 6  # query source + multits sources
    assert len(structure_results.sinks) == 3  # number of appendable ts tables

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    for snk in structure_results.sinks:
        assert snk == get_sink_by_id(snk.id)

    all_sources = get_sources()
    assert len(all_sources) == 10
    assert "Table table2" in {src.name for src in all_sources}
    assert not "Table table1" in {src.name for src in all_sources}
    assert not "Table table3" in {src.name for src in all_sources}

    all_sinks = get_sinks()
    assert len(all_sinks) == 6


@pytest.mark.asyncio
async def test_load_ts_table(three_sqlite_dbs_configured):
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/ro_ts_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": '["a"]',
                    "timestampFrom": "2023-08-01T11:58:02+00:00",
                    "timestampTo": "2023-08-29T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 1
    assert len(received_data["inp"].columns) == 3
    assert "metric" in received_data["inp"].columns
    assert "value" in received_data["inp"].columns
    assert "timestamp" in received_data["inp"].columns

    # metadata there?
    assert received_data["inp"].attrs == {
        "dataset_metadata": {
            "ref_interval_end_timestamp": "2023-08-29T11:58:02+00:00",
            "ref_interval_start_timestamp": "2023-08-01T11:58:02+00:00",
            "ref_interval_type": "closed",
        },
        "by_metric": {"a": {}},
    }

    # metrics as comma separated list
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/ro_ts_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "a,b",
                    "timestampFrom": "2023-08-01T11:58:02+00:00",
                    "timestampTo": "2023-08-29T12:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 2
    assert len(received_data["inp"].columns) == 3

    # ALL metrics
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/ro_ts_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "ALL",
                    "timestampFrom": "2023-08-01T11:58:02+00:00",
                    "timestampTo": "2023-08-29T23:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 4
    assert len(received_data["inp"].columns) == 3

    # TODO: test combinations of different filters


@pytest.mark.asyncio
async def test_write_ts_table(three_sqlite_dbs_configured):
    dataframe = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2023-07-01T00:00:00+00:00", "2023-07-02T00:00:00+00:00"]),
            "metric": ["test_write", "test_write"],
            "value": [42.8, 49.2],
        }
    )

    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/ts_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "test_write",
                    "timestampFrom": "2023-06-01T11:58:02+00:00",
                    "timestampTo": "2023-09-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 0

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="read_only_timeseries_sqlite_database/appendable_ts_table/ts_table",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/ts_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "test_write",
                    "timestampFrom": "2023-06-01T11:58:02+00:00",
                    "timestampTo": "2023-09-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 2
    assert set(received_data["inp"].columns) == {"timestamp", "metric", "value"}


@pytest.mark.asyncio
async def test_column_mapping(three_sqlite_dbs_configured):
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/table3",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "a",
                    "timestampFrom": "2023-06-01T11:58:02+00:00",
                    "timestampTo": "2023-09-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 2
    assert {"timestamp", "metric", "value"} == set(received_data["inp"].columns)

    table_content = pd.read_sql("table3", get_sql_adapter_config().sql_databases[-1].connection_url)

    assert {"datetime", "tsid", "measurement_val"} == set(table_content.columns)
    assert len(table_content) == 4

    dataframe = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2023-07-01T00:00:00+00:00", "2023-07-02T00:00:00+00:00"]),
            "metric": ["map_test", "map_test"],
            "value": [42.8, 49.2],
        }
    )

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="read_only_timeseries_sqlite_database/appendable_ts_table/table3",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )

    table_content = pd.read_sql("table3", get_sql_adapter_config().sql_databases[-1].connection_url)

    assert {"datetime", "tsid", "measurement_val"} == set(table_content.columns)
    assert len(table_content) == 6

    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/table3",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "map_test",
                    "timestampFrom": "2023-06-01T11:58:02+00:00",
                    "timestampTo": "2023-09-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == 2
    assert {"timestamp", "metric", "value"} == set(received_data["inp"].columns)


def _create_timeseries_mtsf(
    attrs: dict,
    days: int,
    metric: str = "nf",
) -> pd.DataFrame:
    """Helper for deletion test"""
    start = datetime(1949, 5, 23, tzinfo=timezone.utc)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(days)]
    values = list(range(days))

    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(dates),
            "metric": [metric for _ in range(days)],
            "value": values,
        }
    )

    df.attrs = copy.deepcopy(attrs)
    return df


DELETION_ONLY_TEST_CASES = [
    pytest.param(
        {
            "dataset_metadata": {
                "invalidation_interval_start": "1949-05-23T00:00:00+00:00",
                "invalidation_interval_end": "1949-05-27T00:00:00+00:00",
                "only_invalidate": True,
            },
            "by_metric": {"nf": {}},
        },
        5,  # Num of days and values in the mtsf that has dataset_metadata attached
        "Deletion based on invalidation dataset.",
        id="delete_based_on_invalidation_dataset",
    ),
    pytest.param(
        {
            "dataset_metadata": {
                "ref_dataset_discrete": True,
                "ref_interval_start_timestamp": "1949-06-01T00:00:00+00:00",
                "ref_interval_end_timestamp": "1949-06-10T00:00:00+00:00",
                "only_invalidate": True,
            },
            "by_metric": {"nf": {}},
        },
        5,
        "Deletion based on discrete timestamps from the reference dataset.",
        id="delete_based_on_discrete_dataset",
    ),
    pytest.param(
        {
            "dataset_metadata": {
                "ref_interval_start_timestamp": "1949-06-01T00:00:00+00:00",
                "ref_interval_end_timestamp": "1949-06-10T00:00:00+00:00",
                "only_invalidate": True,
            },
            "by_metric": {"nf": {}},
        },
        10,
        "Deletion based on reference dataset.",
        id="delete_based_on_ref_dataset",
    ),
    pytest.param(
        {
            "dataset_metadata": {
                "only_invalidate": True,
            },
            "by_metric": {"nf": {}},
        },
        5,
        "Deletion based on inferred interval",
        id="delete_inferred_dataset",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "attrs, num_days, log_message",  # noqa: PT006
    DELETION_ONLY_TEST_CASES,
)
async def test_deletion(
    caplog,
    three_sqlite_dbs_configured,
    deletion_test_table_size: int,
    attrs: dict,
    num_days: int,
    log_message: str,
):
    """Test multiple deletion scenarios, based on test parameters.

    Args:
        caplog: Fixture to capture logs
        three_sqlite_dbs_configured: Fixture providing test databases
        deletion_test_table_size (int): Number of entries in test table
        attrs (dict): Contains dataset_metadata
        num_days (int): Determines how many days/values are in the test mtsf
        log_message (str): Expected message to be logged during deletion process
    """
    df = _create_timeseries_mtsf(attrs=attrs, days=num_days)

    # Check that table has the correct number of entries
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/deletion_test_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "nf",
                    "timestampFrom": "1949-05-01T11:58:02+00:00",
                    "timestampTo": "1949-07-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == deletion_test_table_size

    # Perform send that triggers deletion
    # Check that the deletion dataset was constructed the right way
    with caplog.at_level(logging.INFO):
        caplog.clear()
        await send_data(
            {
                "outp": FilteredSink(
                    ref_id="read_only_timeseries_sqlite_database/appendable_ts_table/deletion_test_table",
                    ref_id_type="SINK",
                )
            },
            {"outp": df},
            adapter_key="sql-adapter",
        )
        assert log_message in caplog.text

    # Check whether the correct number of entries was deleted
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/deletion_test_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "nf",
                    "timestampFrom": "1949-05-01T11:58:02+00:00",
                    "timestampTo": "1949-07-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )

    assert len(received_data["inp"]) == deletion_test_table_size - num_days


@pytest.mark.asyncio
async def test_deletion_with_write(
    caplog, three_sqlite_dbs_configured, deletion_test_table_size: int
):
    num_days = 5
    metadata = {
        "dataset_metadata": {
            "invalidation_interval_start": "1949-05-23T00:00:00+00:00",
            "invalidation_interval_end": "1949-05-27T00:00:00+00:00",
        },
        "by_metric": {"nf": "dn"},
    }
    df = _create_timeseries_mtsf(attrs=metadata, days=num_days)

    # Check that table has the correct number of entries
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/deletion_test_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "nf",
                    "timestampFrom": "1949-05-01T11:58:02+00:00",
                    "timestampTo": "1949-07-01T11:58:02+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )
    assert len(received_data["inp"]) == deletion_test_table_size

    # Perform send that triggers deletion
    with caplog.at_level(logging.INFO):
        caplog.clear()
        await send_data(
            {
                "outp": FilteredSink(
                    ref_id="read_only_timeseries_sqlite_database/appendable_ts_table/deletion_test_table",
                    ref_id_type="SINK",
                )
            },
            {"outp": df},
            adapter_key="sql-adapter",
        )
        assert "Deletion based on invalidation dataset." in caplog.text

    # Check that the entries were replaced
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="read_only_timeseries_sqlite_database/ts_table/deletion_test_table",
                ref_id_type="SOURCE",
                filters={
                    "metrics": "nf",
                    "timestampFrom": "1949-05-23T00:00:00+00:00",
                    "timestampTo": "1949-05-27T00:00:00+00:00",
                },
            )
        },
        adapter_key="sql-adapter",
    )

    assert received_data["inp"]["value"].to_list() == list(range(num_days))
