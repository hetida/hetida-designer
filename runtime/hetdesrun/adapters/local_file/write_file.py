import datetime
import logging
import os
from typing import Any

import pandas as pd

from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterHandlingException,
)
from hetdesrun.adapters.local_file.detect import LocalFile
from hetdesrun.adapters.local_file.structure import get_local_file_by_id
from hetdesrun.adapters.local_file.utils import (
    from_url_representation,
    to_url_representation,
)
from hetdesrun.runtime.logging import _get_job_id_context

logger = logging.getLogger(__name__)


def create_local_file_path_for_generic_any_sink(sink_id: str, filters: dict[str, str]) -> str:
    parent_id = sink_id.removeprefix("GENERIC_ANY_SINK_AT_")
    current_job_id = _get_job_id_context()["currently_executed_job_id"]
    try:
        file_name = filters["file_name"]
    except KeyError:
        return (
            from_url_representation(parent_id)
            + os.sep
            + (
                datetime.datetime.now(datetime.timezone.utc).isoformat()
                + "_"
                + str(current_job_id)
                + ".pkl"
            )
        )
    else:
        ext = os.path.splitext(file_name)[1]
        if ext not in (".pkl", ".h5"):
            msg = (
                f"Provided value '{file_name}' for the filter 'file_name' "
                f"at generic any sink at {from_url_representation(parent_id)} invalid! "
                'The file name must end with ".pkl" or ".h5".'
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg)
        return from_url_representation(parent_id) + os.sep + file_name


def create_local_file_path_for_generic_dataframe_sink(sink_id: str, filters: dict[str, str]) -> str:
    parent_id = sink_id.removeprefix("GENERIC_DATAFRAME_SINK_AT_")
    current_job_id = _get_job_id_context()["currently_executed_job_id"]
    try:
        file_name = filters["file_name"]
    except KeyError:
        return (
            from_url_representation(parent_id)
            + os.sep
            + (
                datetime.datetime.now(datetime.timezone.utc).isoformat()
                + "_"
                + str(current_job_id)
                + ".csv"
            )
        )
    else:
        ext = os.path.splitext(file_name)[1]
        if ext not in (".csv", ".xlsx", ".parquet"):
            msg = (
                f"Provided value '{file_name}' for the filter 'file_name' at "
                f"generic dataframe sink at {from_url_representation(parent_id)} invalid! "
                'The file name must end with ".csv", ".xlsx" or ".parquet".'
            )
            logger.error(msg)
            raise AdapterClientWiringInvalidError(msg)
        return from_url_representation(parent_id) + os.sep + file_name


def obtain_possible_local_sink_file(sink_id: str, filters: dict[str, str]) -> LocalFile | None:
    if sink_id.startswith("GENERIC_"):
        if sink_id.startswith("GENERIC_ANY_SINK_AT_"):
            local_file_path = create_local_file_path_for_generic_any_sink(sink_id, filters)
        if sink_id.startswith("GENERIC_DATAFRAME_SINK_AT_"):
            local_file_path = create_local_file_path_for_generic_dataframe_sink(sink_id, filters)
        possible_local_file = get_local_file_by_id(
            to_url_representation(local_file_path), verify_existence=False
        )
        assert possible_local_file is not None  # for mypy # noqa: S101
        assert (  # noqa: S101
            possible_local_file.parsed_settings_file is not None
        )  # for mypy

        possible_local_file.parsed_settings_file.writable = True

    else:
        possible_local_file = get_local_file_by_id(sink_id)
    return possible_local_file


def write_to_file(data_obj: Any, sink_id: str, filters: dict[str, str]) -> None:
    possible_local_file = obtain_possible_local_sink_file(sink_id, filters)

    if possible_local_file is None:
        raise AdapterHandlingException(
            f"Local file {from_url_representation(sink_id)} target could not be located or "
            "does not lie in a configured local dir or does not exist / is not writable"
        )

    write_kwargs = {}
    if possible_local_file.parsed_settings_file is not None:
        if possible_local_file.parsed_settings_file.writable:
            if possible_local_file.parsed_settings_file.write_settings is not None:
                write_kwargs = possible_local_file.parsed_settings_file.write_settings
        else:
            raise AdapterHandlingException(
                f"Local file {possible_local_file.path} settings file does not allow writing!"
            )

    file_support_handler = possible_local_file.file_support_handler()

    if file_support_handler is None:
        raise AdapterHandlingException(
            f"Local file {possible_local_file.path} has unknown/unregistered file extension."
        )
    if file_support_handler.write_handler_func is None:
        raise AdapterHandlingException(
            f"Registered FileSupportHandler for file {possible_local_file.path} has no "
            "write_handler_func."
        )

    try:
        file_support_handler.write_handler_func(data_obj, possible_local_file.path, **write_kwargs)
    except Exception as e:  # noqa: BLE001
        msg = (
            f"Failed to write local file \n{str(possible_local_file)}\n with "
            f"file_support_handler \n{str(file_support_handler)}\nException was:\n{str(e)}."
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    logger.info(
        "Finished writing local file \n%s\n with file_support_handler \n%s",
        str(possible_local_file),
        str(file_support_handler),
    )
    if isinstance(data_obj, pd.DataFrame):
        logger.info("Written DataFrame of shape %s:\n%s", str(data_obj.shape), str(data_obj))
