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


def test_config_works(two_sqlite_dbs_configured):
    assert len(get_sql_adapter_config().sql_databases) == 2


def test_sql_adapter_structure(two_sqlite_dbs_configured):
    structure_results = get_structure()
    assert len(structure_results.thingNodes) == 2
    assert len(structure_results.sources) == 0
    assert len(structure_results.sinks) == 0

    # readable sqlite db
    structure_results = get_structure("test_example_sqlite_read_db")
    assert len(structure_results.thingNodes) == 0
    assert len(structure_results.sources) == 3
    assert len(structure_results.sinks) == 0

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    # writabel sqlite db
    structure_results = get_structure("test_writable_temp_sqlite_db")
    assert len(structure_results.thingNodes) == 0
    assert (
        len(structure_results.sources) == 1
    )  # since nothing is written yet, only query source

    for src in structure_results.sources:
        assert src == get_source_by_id(src.id)

    assert structure_results.sources[0].id == "test_writable_temp_sqlite_db/query"
    source_query_filter = structure_results.sources[0].filters["sql_query"]
    assert source_query_filter["type"] == "free_text"
    assert len(structure_results.sinks) == 3

    for snk in structure_results.sinks:
        assert snk == get_sink_by_id(snk.id)

    # get all sources
    all_sources = get_sources()
    assert len(all_sources) == 4
    for src in all_sources:
        assert src == get_source_by_id(src.id)

    # get all sinks
    all_sinks = get_sinks()
    assert len(all_sinks) == 3
    for snk in all_sinks:
        assert snk == get_sink_by_id(snk.id)


@pytest.mark.asyncio
async def test_roundtrip_append_table(two_sqlite_dbs_configured):
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_example_sqlite_read_db/table/data_table",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    dataframe = received_data["inp"]
    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 3

    with pytest.raises(ValueError):
        await load_data(
            {
                "inp": FilteredSource(
                    ref_id="test_writable_temp_sqlite_db/table/append_alert_table",
                    ref_id_type="SOURCE",
                )
            },
            adapter_key="sql-adapter",
        )

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="test_writable_temp_sqlite_db/append_table/append_alert_table",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )

    append_table_after_write = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_writable_temp_sqlite_db/table/append_alert_table",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    assert len(append_table_after_write["inp"]) == 3

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="test_writable_temp_sqlite_db/append_table/append_alert_table",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )

    append_table_after_second_write = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_writable_temp_sqlite_db/table/append_alert_table",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    assert len(append_table_after_second_write["inp"]) == 6


@pytest.mark.asyncio
async def test_roundtrip_replace_table(two_sqlite_dbs_configured):
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_example_sqlite_read_db/table/data_table",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    dataframe = received_data["inp"]
    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 3

    with pytest.raises(ValueError):
        await load_data(
            {
                "inp": FilteredSource(
                    ref_id="test_writable_temp_sqlite_db/table/model_config_params",
                    ref_id_type="SOURCE",
                )
            },
            adapter_key="sql-adapter",
        )

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="test_writable_temp_sqlite_db/replace_table/model_config_params",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )

    replace_table_after_write = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_writable_temp_sqlite_db/table/model_config_params",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    assert len(replace_table_after_write["inp"]) == 3

    await send_data(
        {
            "outp": FilteredSink(
                ref_id="test_writable_temp_sqlite_db/replace_table/model_config_params",
                ref_id_type="SINK",
            )
        },
        {"outp": dataframe},
        adapter_key="sql-adapter",
    )

    replace_table_after_second_write = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_writable_temp_sqlite_db/table/model_config_params",
                ref_id_type="SOURCE",
            )
        },
        adapter_key="sql-adapter",
    )

    assert len(replace_table_after_second_write["inp"]) == 3
