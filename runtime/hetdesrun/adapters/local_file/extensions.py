from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, validator

from hetdesrun.adapters.generic_rest.external_types import ExternalType


class FileSupportHandler(BaseModel):
    associated_extensions: list[str]
    read_handler_func: Callable | None = None
    write_handler_func: Callable | None = None
    adapter_data_type: ExternalType = Field(
        ExternalType.DATAFRAME,
        description="As which type the adapter should offer files.",
    )

    @validator("write_handler_func", always=True)
    def at_least_one_handler_func(cls, v: Any, values: dict[str, Any]) -> Callable | None:
        if (values["read_handler_func"] is None) and (values["write_handler_func"] is None):
            raise ValueError(
                "At least one of read_handler_func or write_handler_func must be provided."
            )
        return v  # type: ignore


handlers_by_extension: dict[str, FileSupportHandler] = {}


def get_file_support_handler(path: str) -> FileSupportHandler | None:
    """Get corresponding file support handler for the given path's extension

    This returns the first matching handler where ordering depends on Pythons dict keys ordering
    based on the order of registration.
    """
    for registered_extension in handlers_by_extension:
        if path.endswith(registered_extension):
            return handlers_by_extension[registered_extension]

    return None


def register_file_support(
    file_support_handler: FileSupportHandler, allow_overwrite: bool = False
) -> None:
    """Registers a new file support handler

    By default does not allow to overwriting existing file support handler registrations for an
    extension. This can be changed by setting allow_overwrite to True.

    It is recommended to avoid registering extensions where finding the handler may depend on
    ordering, i.e. do not register both "a.b" and "b" as extensions since the handler for "b" may be
    selected for a file with name myfile.a.b
    """

    for extension in file_support_handler.associated_extensions:
        if (not allow_overwrite) and (handlers_by_extension.get(extension) is not None):
            raise KeyError(
                f"Found existing registered extension {extension}."
                " Cannot overwrite since allow_overwrite==False."
            )
        handlers_by_extension[extension] = file_support_handler
