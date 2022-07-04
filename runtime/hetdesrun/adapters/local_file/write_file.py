import logging

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.local_file.structure import get_local_file_by_id
from hetdesrun.adapters.local_file.utils import from_url_representation

logger = logging.getLogger(__name__)


def write_to_file(df: pd.DataFrame, sink_id: str) -> None:
    possible_local_file = get_local_file_by_id(sink_id)

    if possible_local_file is None:
        raise AdapterHandlingException(
            f"Local file {from_url_representation(sink_id)} target could not be located or"
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
        file_support_handler.write_handler_func(
            df, possible_local_file.path, **write_kwargs
        )
    except Exception as e:
        msg = (
            f"Failed to write local file \n{str(possible_local_file)}\n with "
            f"file_support_handler \n{str(file_support_handler)}\nException was:\n{str(e)}."
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e
    logger.info(
        "Finished writing local file \n%s\n with file_support_handler \n%s\n"
        " Written DataFrame of shape %s:\n%s",
        str(possible_local_file),
        str(file_support_handler),
        str(df.shape),
        str(df),
    )
