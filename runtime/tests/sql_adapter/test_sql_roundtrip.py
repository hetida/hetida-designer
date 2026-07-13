import pandas as pd
import pytest
from sqlalchemy import create_engine, inspect

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.sql_adapter import load_data, send_data
from hetdesrun.models.data_selection import FilteredSink, FilteredSource


@pytest.mark.asyncio
async def test_load_query_table(two_sqlite_dbs_configured):
    received_data = await load_data(
        {
            "inp": FilteredSource(
                ref_id="test_example_sqlite_read_db/query",
                ref_id_type="SOURCE",
                filters={"sql_query": "SELECT a FROM data_table"},
            )
        },
        adapter_key="sql-adapter",
    )

    assert received_data["inp"].columns == ["a"]


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

    with pytest.raises(ValueError):  # noqa: PT011
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
async def test_write_to_table_not_configured_as_sink_is_rejected(
    two_sqlite_dbs_configured, temporary_sqlite_file_path
):
    dataframe = pd.DataFrame({"a": [1, 2, 3]})

    # append to a table that is not in append_tables
    with pytest.raises(AdapterHandlingException, match="not allowed"):
        await send_data(
            {
                "outp": FilteredSink(
                    ref_id="test_writable_temp_sqlite_db/append_table/secret_table",
                    ref_id_type="SINK",
                )
            },
            {"outp": dataframe},
            adapter_key="sql-adapter",
        )

    # replace a table that is only configured as an append table (mode-specific check)
    with pytest.raises(AdapterHandlingException, match="not allowed"):
        await send_data(
            {
                "outp": FilteredSink(
                    ref_id="test_writable_temp_sqlite_db/replace_table/model_run_stats",
                    ref_id_type="SINK",
                )
            },
            {"outp": dataframe},
            adapter_key="sql-adapter",
        )

    # the rejected writes must not have created/touched any table
    engine = create_engine("sqlite+pysqlite:///" + temporary_sqlite_file_path)
    try:
        existing_tables = inspect(engine).get_table_names()
    finally:
        engine.dispose()
    assert "secret_table" not in existing_tables


@pytest.mark.asyncio
async def test_read_table_not_configured_as_source_is_rejected(
    three_sqlite_dbs_configured,
):
    db_key = "read_only_timeseries_sqlite_database"

    # table1 is an existing table but explicitly ignored via ignore_tables
    with pytest.raises(AdapterHandlingException, match="not allowed"):
        await load_data(
            {"inp": FilteredSource(ref_id=f"{db_key}/table/table1", ref_id_type="SOURCE")},
            adapter_key="sql-adapter",
        )

    # deletion_test_table exists but is not in explicit_source_tables
    with pytest.raises(AdapterHandlingException, match="not allowed"):
        await load_data(
            {
                "inp": FilteredSource(
                    ref_id=f"{db_key}/table/deletion_test_table", ref_id_type="SOURCE"
                )
            },
            adapter_key="sql-adapter",
        )

    # a timeseries table must not be readable through the ordinary dataframe table source
    with pytest.raises(AdapterHandlingException, match="not allowed"):
        await load_data(
            {"inp": FilteredSource(ref_id=f"{db_key}/table/ts_table", ref_id_type="SOURCE")},
            adapter_key="sql-adapter",
        )

    # table2 is in explicit_source_tables and not ignored: it may be read
    received = await load_data(
        {"inp": FilteredSource(ref_id=f"{db_key}/table/table2", ref_id_type="SOURCE")},
        adapter_key="sql-adapter",
    )
    assert isinstance(received["inp"], pd.DataFrame)


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

    with pytest.raises(ValueError):  # noqa PT011
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
