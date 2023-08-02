from unittest import mock

import pandas as pd
import pytest

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.local_file.utils import to_url_representation
from hetdesrun.adapters.local_file.write_file import (
    write_to_file,
)


def test_local_file_adapter_write_to_file_existing_file_without_filters():
    data_obj = pd.DataFrame({"a": [1, 2, 3], "b": [12.2, 13.3, 14.4]})
    file_path = "tests/data/local_files/dir1/overwritable_excel_file.xlsx"
    sink_id = to_url_representation(file_path)
    filters = {}

    with mock.patch(
        "hetdesrun.adapters.local_file.write_file.pd.DataFrame.to_excel"
    ) as to_excel_mock:
        write_to_file(data_obj, sink_id, filters)

    assert to_excel_mock.called_once
    _, args, kwargs = to_excel_mock.mock_calls[0]
    assert kwargs == {}
    assert len(args) == 1
    assert args[0] == "tests/data/local_files/dir1/overwritable_excel_file.xlsx"


def test_local_file_adapter_write_to_file_non_existing_file_with_filters():
    file_path = "tests/data/local_files/dir1"

    with mock.patch(
        "hetdesrun.adapters.local_file.write_file._get_job_id_context",
        return_value={
            "currently_executed_job_id": "1681ea7e-c57f-469a-ac12-592e3e8665cf"
        },
    ):
        with mock.patch(
            "hetdesrun.adapters.local_file.write_file.LocalFile.file_support_handler"
        ) as file_handler_mock:
            file_handler_mock.write_handler_func()
            data_obj = {"key": "value"}
            any_sink_id = "GENERIC_ANY_SINK_AT_" + to_url_representation(file_path)

            write_to_file(data_obj, any_sink_id, {"file_name": "test.pkl"})

            assert file_handler_mock.called_once
            assert hasattr(file_handler_mock, "write_handler_func")
            assert isinstance(file_handler_mock.write_handler_func, mock.Mock)
            assert file_handler_mock.write_handler_func.called_once
            _, args, kwargs = file_handler_mock.write_handler_func.mock_calls[0]
            assert kwargs == {}
            # assert len(args) == 2
            # assert args[1] == "tests/data/local_files/dir1/test.pkl"

            with pytest.raises(
                AdapterClientWiringInvalidError, match=r"must end with.*any sink"
            ):
                write_to_file(data_obj, any_sink_id, {"file_name": "test.xlsx"})

        with mock.patch(
            "hetdesrun.adapters.local_file.write_file.pd.DataFrame.to_excel"
        ) as to_excel_mock:
            data_obj = pd.DataFrame({"a": [1, 2, 3], "b": [12.2, 13.3, 14.4]})
            df_sink_id = "GENERIC_DATAFRAME_SINK_AT_" + to_url_representation(file_path)

            write_to_file(data_obj, df_sink_id, {"file_name": "test.xlsx"})

            assert to_excel_mock.called_once
            _, args, kwargs = to_excel_mock.mock_calls[0]
            assert kwargs == {}
            assert len(args) == 1
            assert args[0] == "tests/data/local_files/dir1/test.xlsx"

        with pytest.raises(
            AdapterClientWiringInvalidError, match=r"must end with.*dataframe sink"
        ):
            write_to_file(data_obj, df_sink_id, {"file_name": "test.pkl"})
