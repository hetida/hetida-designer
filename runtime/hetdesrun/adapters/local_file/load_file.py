import logging

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.local_file.structure import get_local_file_by_id
from hetdesrun.adapters.local_file.utils import from_url_representation

logger = logging.getLogger(__name__)


def load_file_from_id(source_id: str) -> pd.DataFrame:
    possible_local_file = get_local_file_by_id(source_id)

    if possible_local_file is None:
        raise AdapterHandlingException(
            f"Local file {from_url_representation(source_id)} could not be located or"
            "does not lie in a configured local dir or does not exist"
        )

    read_kwargs = {}
    if possible_local_file.parsed_settings_file is not None:
        if possible_local_file.parsed_settings_file.loadable:
            if possible_local_file.parsed_settings_file.load_settings is not None:
                read_kwargs = possible_local_file.parsed_settings_file.load_settings
        else:
            raise AdapterHandlingException(
                f"Local file {possible_local_file.path} settings file does not allow loading!"
            )

    file_support_handler = possible_local_file.file_support_handler()

    if file_support_handler is None:
        raise AdapterHandlingException(
            f"Local file {possible_local_file.path} has unknown/unregistered file extension."
        )

    if file_support_handler.read_handler_func is None:
        raise AdapterHandlingException(
            f"Registered FileSupportHandler for file {possible_local_file.path} has no "
            "read_handler_func."
        )

    # Actual loading
    try:
        loaded_df = file_support_handler.read_handler_func(
            possible_local_file.path, **read_kwargs
        )
    except Exception as e:
        msg = (
            f"Failed to retrieve local file \n{str(possible_local_file)}\n with "
            f"file_support_handler \n{str(file_support_handler)}\nException was:\n{str(e)}."
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    logger.info(
        "Finished retrieving local file \n%s\n with file_support_handler \n%s\n"
        " Resulting DataFrame of shape %s:\n%s",
        str(possible_local_file),
        str(file_support_handler),
        str(loaded_df.shape),
        str(loaded_df),
    )
    return loaded_df
