"""Runtime part of hetida designer data adapter system

The adapter system allows to register adapters for accessing external
data sources and data sinks.

This module contains tooling around registering adapters and generic
load / send functionality.

See the hetdesrun_config.py file in runtime main directory for hints / docs
on registering your own data adapters.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from hetdesrun.adapters.exceptions import (  # noqa: F401
    AdapterClientWiringInvalidError,
    AdapterConnectionError,
    AdapterHandlingException,
    AdapterOutputDataError,
    AdapterUnknownError,
)
from hetdesrun.adapters.generic_rest import load_data as generic_rest_adapter_load_func
from hetdesrun.adapters.generic_rest import send_data as generic_rest_adapter_send_func
from hetdesrun.adapters.local_file import load_data as local_file_load_data
from hetdesrun.adapters.local_file import send_data as local_file_send_data
from hetdesrun.adapters.sink.direct_provisioning import send_directly_provisioned_data
from hetdesrun.adapters.source.direct_provisioning import load_directly_provisioned_data
from hetdesrun.models.data_selection import FilteredSink, FilteredSource

ConnectionErrorTuple = (
    tuple[type[AdapterConnectionError]]
    | tuple[type[AdapterConnectionError], type[Exception]]
)

OutputDataErrorTuple = (
    tuple[type[AdapterOutputDataError]]
    | tuple[type[AdapterOutputDataError], type[Exception]]
)

ClientWiringInvalidErrorTuple = (
    tuple[type[AdapterClientWiringInvalidError]]
    | tuple[type[AdapterClientWiringInvalidError], type[Exception]]
)

logger = logging.getLogger(__name__)


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


def prepare_exc_classes(
    connection_custom_error: type[Exception] | None = None,
    output_data_custom_error: type[Exception] | None = None,
    client_wiring_invalid_error_class: type[Exception] | None = None,
) -> tuple[ConnectionErrorTuple, OutputDataErrorTuple, ClientWiringInvalidErrorTuple]:
    """Gather existing and custom exception classes for simultaneous handling

    This meachanism allows client adapter implementations to send specific
    exceptions without necessity to import exception classes from runtime.
    """
    connection_exceptions: ConnectionErrorTuple
    if connection_custom_error is not None:
        connection_exceptions = (AdapterConnectionError, connection_custom_error)
    else:
        connection_exceptions = (AdapterConnectionError,)

    output_data_exceptions: OutputDataErrorTuple
    if output_data_custom_error is not None:
        output_data_exceptions = (AdapterOutputDataError, output_data_custom_error)

    else:
        output_data_exceptions = (AdapterOutputDataError,)

    wiring_invalid_exceptions: ClientWiringInvalidErrorTuple
    if client_wiring_invalid_error_class is not None:
        wiring_invalid_exceptions = (
            AdapterClientWiringInvalidError,
            client_wiring_invalid_error_class,
        )
    else:
        wiring_invalid_exceptions = (AdapterClientWiringInvalidError,)

    return connection_exceptions, output_data_exceptions, wiring_invalid_exceptions


(
    default_connection_errors,
    default_output_data_errors,
    default_invalid_wiring_errors,
) = prepare_exc_classes(
    connection_custom_error=None,
    output_data_custom_error=None,
    client_wiring_invalid_error_class=None,
)


GENERIC_REST_SOURCE_ADAPTER: SourceAdapter = SourceAdapter(
    load_sources_func=generic_rest_adapter_load_func,
    connection_error_classes=default_connection_errors,
    output_data_error_classes=default_output_data_errors,
    client_wiring_invalid_error_classes=default_invalid_wiring_errors,
)

GENERIC_REST_SINK_ADAPTER: SinkAdapter = SinkAdapter(
    send_sinks_func=generic_rest_adapter_send_func,
    connection_error_classes=default_connection_errors,
    output_data_error_classes=default_output_data_errors,
    client_wiring_invalid_error_classes=default_invalid_wiring_errors,
)


def register_source_adapter(
    adapter_key: int | str,
    load_func: Callable[
        [dict[str, FilteredSource], str],
        dict[str, Any] | Awaitable[dict[str, Any]],
    ],
    connection_error_class: type[Exception] | None = None,
    output_data_error_class: type[Exception] | None = None,
    client_wiring_invalid_error_class: type[Exception] | None = None,
) -> None:
    connection_errors, output_data_errors, invalid_wiring_errors = prepare_exc_classes(
        connection_custom_error=connection_error_class,
        output_data_custom_error=output_data_error_class,
        client_wiring_invalid_error_class=client_wiring_invalid_error_class,
    )
    SOURCE_ADAPTERS[adapter_key] = SourceAdapter(
        load_sources_func=load_func,
        connection_error_classes=connection_errors,
        output_data_error_classes=output_data_errors,
        client_wiring_invalid_error_classes=invalid_wiring_errors,
    )


def register_sink_adapter(
    adapter_key: int | str,
    send_func: Callable[
        [dict[str, FilteredSink], dict[str, Any], str],
        dict[str, Any] | Awaitable[dict[str, Any]],
    ],
    connection_error_class: type[Exception] | None = None,
    output_data_error_class: type[Exception] | None = None,
    client_wiring_invalid_error_class: type[Exception] | None = None,
) -> None:
    connection_errors, output_data_errors, invalid_wiring_errors = prepare_exc_classes(
        connection_custom_error=connection_error_class,
        output_data_custom_error=output_data_error_class,
        client_wiring_invalid_error_class=client_wiring_invalid_error_class,
    )
    SINK_ADAPTERS[adapter_key] = SinkAdapter(
        send_sinks_func=send_func,
        connection_error_classes=connection_errors,
        output_data_error_classes=output_data_errors,
        client_wiring_invalid_error_classes=invalid_wiring_errors,
    )


# Registering direct provisioning adapters

register_source_adapter(
    adapter_key=1,
    load_func=load_directly_provisioned_data,
)

register_source_adapter(
    adapter_key="direct_provisioning",
    load_func=load_directly_provisioned_data,
)

register_sink_adapter(
    adapter_key=1,
    send_func=send_directly_provisioned_data,
)

register_sink_adapter(
    adapter_key="direct_provisioning",
    send_func=send_directly_provisioned_data,
)


# Registering local file adapter

register_source_adapter(
    adapter_key="local-file-adapter", load_func=local_file_load_data
)

register_sink_adapter(adapter_key="local-file-adapter", send_func=local_file_send_data)


def get_source_adapter(adapter_key: int | str) -> SourceAdapter:
    try:
        return SOURCE_ADAPTERS[adapter_key]
    except KeyError:
        if isinstance(adapter_key, str):
            return GENERIC_REST_SOURCE_ADAPTER
        raise AdapterUnknownError(
            f"No client source adapter with id {str(adapter_key)} registered in runtime!"
        ) from None


def get_sink_adapter(adapter_key: int | str) -> SinkAdapter:
    try:
        return SINK_ADAPTERS[adapter_key]
    except KeyError:
        if isinstance(adapter_key, str):
            return GENERIC_REST_SINK_ADAPTER
        raise AdapterUnknownError(
            f"No client sink adapter with id {str(adapter_key)} registered in runtime!"
        ) from None


async def load_data_from_adapter(
    adapter_key: str | int,
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
) -> dict[str, Any]:
    """Generic data loading from adapter

    Returns a dictionary with workflow input names as keys and the corresponding loaded data
    as values. If adapter_key is a String and there is no registered adapter with this key it
    defaults to the generic rest adapter.
    """

    adapter = get_source_adapter(adapter_key)

    adapter_func = adapter["load_sources_func"]

    try:
        loaded_data: dict[str, Any]
        if asyncio.iscoroutinefunction(adapter_func):
            loaded_data = await adapter_func(
                wf_input_name_to_filtered_source_mapping_dict,
                adapter_key=str(adapter_key),
            )
            return loaded_data
        loaded_data = adapter_func(
            wf_input_name_to_filtered_source_mapping_dict, adapter_key=str(adapter_key)
        )
        return loaded_data
    except adapter["connection_error_classes"] as e:
        if isinstance(e, AdapterConnectionError):
            raise e
        raise AdapterConnectionError(
            f"Adapter Client specific connection error:\n{str(e)}"
        ) from e
    except adapter["output_data_error_classes"] as e:
        if isinstance(e, AdapterOutputDataError):
            raise e
        raise AdapterOutputDataError(
            f"Adapter Client specific output data error:\n{str(e)}"
        ) from e
    except adapter["client_wiring_invalid_error_classes"] as e:
        if isinstance(e, AdapterClientWiringInvalidError):
            raise e
        raise AdapterClientWiringInvalidError(
            f"Adapter Client wiring invalid error:\n{str(e)}"
        ) from e


async def send_data_with_adapter(
    adapter_key: int | str,
    wf_output_name_to_filtered_sink_mapping_dict: dict,
    result_data: dict,
) -> dict[str, Any] | None:
    """Generic data emitting using adapter

    If adapter_key is a String and there is no registered adapter with this key it
    defaults to the generic rest adapter.
    """
    adapter = get_sink_adapter(adapter_key)

    adapter_func = adapter["send_sinks_func"]

    try:
        data_not_sent: dict[str, Any] | None = {}
        if asyncio.iscoroutinefunction(adapter_func):
            data_not_sent = await adapter_func(
                wf_output_name_to_filtered_sink_mapping_dict,
                result_data,
                adapter_key=str(adapter_key),
            )
        else:
            data_not_sent = adapter_func(
                wf_output_name_to_filtered_sink_mapping_dict,
                result_data,
                adapter_key=str(adapter_key),
            )

    except adapter["connection_error_classes"] as e:
        if isinstance(e, AdapterConnectionError):
            raise e
        raise AdapterConnectionError(
            f"Adapter Client specific connection error:\n{str(e)}"
        ) from e
    except adapter["output_data_error_classes"] as e:
        if isinstance(e, AdapterOutputDataError):
            raise e
        raise AdapterOutputDataError(
            f"Adapter Client specific output data error:\n{str(e)}"
        ) from e
    except adapter["client_wiring_invalid_error_classes"] as e:
        if isinstance(e, AdapterClientWiringInvalidError):
            raise e
        raise AdapterClientWiringInvalidError(
            f"Adapter Client wiring invalid error:\n{str(e)}"
        ) from e
    if data_not_sent is None:
        data_not_sent = {}
    logger.info(
        "Data not sent with adapter %s workflow output names: %s",
        adapter_key,
        str(list(data_not_sent.keys())),
    )
    return data_not_sent
