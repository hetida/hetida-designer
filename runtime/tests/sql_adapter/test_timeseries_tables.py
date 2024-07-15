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
    assert len(structure_results.sources) == 5  # query source + multits sources
    assert len(structure_results.sinks) == 2  # the one ts table which is appendable

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    for snk in structure_results.sinks:
        assert snk == get_sink_by_id(snk.id)

    all_sources = get_sources()
    assert len(all_sources) == 9
    assert "Table table2" in {src.name for src in all_sources}
    assert not "Table table1" in {src.name for src in all_sources}
    assert not "Table table3" in {src.name for src in all_sources}

    all_sinks = get_sinks()
    assert len(all_sinks) == 5


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
        "ref_interval_end_timestamp": "2023-08-29T11:58:02+00:00",
        "ref_interval_start_timestamp": "2023-08-01T11:58:02+00:00",
        "ref_interval_type": "closed",
        "ref_metrics": ["a"],
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
