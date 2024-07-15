from collections.abc import Callable
from typing import TypedDict

from hetdesrun.adapters.exceptions import (  # noqa: F401
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
    AdapterHandlingException,
    AdapterOutputDataError,
    AdapterUnknownError,
)

ConnectionErrorTuple = (
    tuple[type[AdapterConnectionError]] | tuple[type[AdapterConnectionError], type[Exception]]
)

OutputDataErrorTuple = (
    tuple[type[AdapterOutputDataError]] | tuple[type[AdapterOutputDataError], type[Exception]]
)

ClientWiringInvalidErrorTuple = (
    tuple[type[AdapterClientWiringInvalidError]]
    | tuple[type[AdapterClientWiringInvalidError], type[Exception]]
)


class SourceAdapter(TypedDict):
    load_sources_func: Callable
    connection_error_classes: ConnectionErrorTuple
    output_data_error_classes: OutputDataErrorTuple
    client_wiring_invalid_error_classes: ClientWiringInvalidErrorTuple


class SinkAdapter(TypedDict):
    send_sinks_func: Callable
    connection_error_classes: ConnectionErrorTuple
    output_data_error_classes: OutputDataErrorTuple
    client_wiring_invalid_error_classes: ClientWiringInvalidErrorTuple


SOURCE_ADAPTERS: dict[int | str, SourceAdapter] = {}

SINK_ADAPTERS: dict[int | str, SinkAdapter] = {}
