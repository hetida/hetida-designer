import pandas as pd
import pytest

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
