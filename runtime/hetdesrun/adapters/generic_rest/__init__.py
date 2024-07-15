"""Generic REST adapter runtime implementation

This implements source and sink runtime adapter client for the generic rest adapter.
"""

import asyncio
from collections.abc import Mapping
from typing import Any, TypeVar

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.generic_rest.external_types import ExternalType, GeneralType
from hetdesrun.adapters.generic_rest.load_dataframe import load_dataframes_from_adapter
from hetdesrun.adapters.generic_rest.load_metadata import load_multiple_metadata
from hetdesrun.adapters.generic_rest.load_multitsframe import (
    load_multitsframes_from_adapter,
)
from hetdesrun.adapters.generic_rest.load_ts_data import (
    load_grouped_timeseries_data_together,
)
from hetdesrun.adapters.generic_rest.send_dataframe import send_dataframes_to_adapter
from hetdesrun.adapters.generic_rest.send_metadata import (
    send_multiple_metadata_to_adapter,
)
from hetdesrun.adapters.generic_rest.send_multitsframe import (
    send_multitsframes_to_adapter,
)
from hetdesrun.adapters.generic_rest.send_ts_data import (
    send_multiple_timeseries_to_adapter,
)
from hetdesrun.models.data_selection import FilteredSink, FilteredSource


def validate_type_and_ref_id(
    wf_in_out_name_to_filtered_source_or_sink_mapping: Mapping[str, FilteredSource | FilteredSink],
) -> tuple[list[str], list[str], list[ExternalType]]:
    """Validate generic rest adapter specific requirements of wirings

    * ref_ids can't be None
    * types must be provided and be a known rest adapter type

    Raises AdapterClientWiringInvalidError if requirements are not fullfilled.

    Returns a triple of compatibly ordered lists of
        workflow input / output names
        ref ids
        types (ExternalType)
    """

    wf_in_out_names = list(wf_in_out_name_to_filtered_source_or_sink_mapping.keys())
    ref_ids: list[str] = [
        filtered_source.ref_id  # type: ignore
        for wf_input_name in wf_in_out_names
        if (
            filtered_source := wf_in_out_name_to_filtered_source_or_sink_mapping[wf_input_name]
        ).ref_id
        is not None
    ]

    if len(ref_ids) < len(wf_in_out_name_to_filtered_source_or_sink_mapping):
        raise AdapterClientWiringInvalidError(
            "Unset ref id in a wiring using generic rest adapter."
        )

    try:
        corresponding_types: list[ExternalType] = [
            ExternalType(fs.type)
            for wf_input_name in wf_in_out_names
            if (fs := wf_in_out_name_to_filtered_source_or_sink_mapping[wf_input_name]).type
            is not None
        ]
    except ValueError as e:
        raise AdapterClientWiringInvalidError(
            "Unknown type in a wiring using generic rest adapter."
        ) from e

    if len(corresponding_types) < len(wf_in_out_name_to_filtered_source_or_sink_mapping):
        raise AdapterClientWiringInvalidError("Unset type in a wiring using generic rest adapter.")

    if not all(
        isinstance(rest_adapter_data_type, ExternalType)
        for rest_adapter_data_type in corresponding_types
    ):
        raise AdapterClientWiringInvalidError("Got unknown type in wiring for generic rest adapter")

    return wf_in_out_names, ref_ids, corresponding_types


FilteredSourceSink = TypeVar("FilteredSourceSink", FilteredSource, FilteredSink)


def validate_metadatum_filtered_source_sink(
    filtered_source_sink: FilteredSourceSink,
) -> FilteredSourceSink:
    if filtered_source_sink.ref_id_type is None:
        raise AdapterClientWiringInvalidError("Unset ref_id_type in metadatum wiring.")
    if filtered_source_sink.ref_key is None:
        raise AdapterClientWiringInvalidError("Unset ref_key in metadatum wiring.")
    return filtered_source_sink


async def load_data(
    wf_input_name_to_filtered_source_mapping_dict: dict[str, FilteredSource],
    adapter_key: str,
) -> dict[str, Any]:
    """load data from generic rest adapter"""

    wf_input_names, _, parsed_source_types = validate_type_and_ref_id(
        wf_input_name_to_filtered_source_mapping_dict
    )

    # Organize by type
    metadata_data_to_load: dict[str, FilteredSource] = {}
    timeseries_data_to_load: dict[str, FilteredSource] = {}
    series_data_to_load: dict[str, FilteredSource] = {}
    dataframe_data_to_load: dict[str, FilteredSource] = {}
    multitsframe_data_to_load: dict[str, FilteredSource] = {}

    for wf_input_name, parsed_source_type in zip(wf_input_names, parsed_source_types, strict=True):
        entry = wf_input_name_to_filtered_source_mapping_dict[wf_input_name]
        entry.type = parsed_source_type

        if entry.type.general_type == GeneralType.METADATA:
            metadata_data_to_load[wf_input_name] = validate_metadatum_filtered_source_sink(entry)
        elif entry.type.general_type == GeneralType.TIMESERIES:
            timeseries_data_to_load[wf_input_name] = entry
        elif entry.type.general_type == GeneralType.SERIES:
            series_data_to_load[wf_input_name] = entry
        elif entry.type.general_type == GeneralType.DATAFRAME:
            dataframe_data_to_load[wf_input_name] = entry
        elif entry.type.general_type == GeneralType.MULTITSFRAME:
            multitsframe_data_to_load[wf_input_name] = entry

    (
        loaded_ts_data,
        loaded_dataframes,
        loaded_multitsframes,
        loaded_metadata,
    ) = await asyncio.gather(
        load_grouped_timeseries_data_together(timeseries_data_to_load, adapter_key=adapter_key),
        load_dataframes_from_adapter(dataframe_data_to_load, adapter_key=adapter_key),
        load_multitsframes_from_adapter(multitsframe_data_to_load, adapter_key=adapter_key),
        load_multiple_metadata(metadata_data_to_load, adapter_key=adapter_key),
    )

    return {
        **loaded_ts_data,
        **loaded_dataframes,
        **loaded_multitsframes,
        **loaded_metadata,
    }


async def send_data(
    wf_output_name_to_filtered_sink_mapping_dict: dict[str, FilteredSink],
    wf_output_name_to_value_mapping_dict: dict[str, Any],
    adapter_key: str,
) -> dict[str, Any]:
    """Send data to generic rest adapter"""

    wf_output_names, _, parsed_sink_types = validate_type_and_ref_id(
        wf_output_name_to_filtered_sink_mapping_dict
    )

    # Organize by type
    metadata_data_to_send: dict[str, Any] = {}
    metadata_filtered_sinks: dict[str, FilteredSink] = {}
    timeseries_data_to_send: dict[str, pd.Series] = {}
    timeseries_filtered_sinks: dict[str, FilteredSink] = {}
    series_data_to_send: dict[str, pd.Series] = {}
    series_filtered_sinks: dict[str, FilteredSink] = {}
    dataframe_data_to_send: dict[str, pd.DataFrame] = {}
    dataframe_filtered_sinks: dict[str, FilteredSink] = {}
    multitsframe_data_to_send: dict[str, pd.DataFrame] = {}
    multitsframe_filtered_sinks: dict[str, FilteredSink] = {}

    for wf_output_name, parsed_sink_type in zip(wf_output_names, parsed_sink_types, strict=True):
        entry = wf_output_name_to_filtered_sink_mapping_dict[wf_output_name]
        entry.type = parsed_sink_type
        value = wf_output_name_to_value_mapping_dict[wf_output_name]

        if entry.type.general_type == GeneralType.METADATA:
            metadata_filtered_sinks[wf_output_name] = validate_metadatum_filtered_source_sink(entry)
            metadata_data_to_send[wf_output_name] = value
        elif entry.type.general_type == GeneralType.TIMESERIES:
            timeseries_filtered_sinks[wf_output_name] = entry
            timeseries_data_to_send[wf_output_name] = value
        elif entry.type.general_type == GeneralType.SERIES:
            series_filtered_sinks[wf_output_name] = entry
            series_data_to_send[wf_output_name] = value
        elif entry.type.general_type == GeneralType.DATAFRAME:
            dataframe_filtered_sinks[wf_output_name] = entry
            dataframe_data_to_send[wf_output_name] = value
        elif entry.type.general_type == GeneralType.MULTITSFRAME:
            multitsframe_filtered_sinks[wf_output_name] = entry
            multitsframe_data_to_send[wf_output_name] = value

    await asyncio.gather(
        send_dataframes_to_adapter(
            dataframe_filtered_sinks, dataframe_data_to_send, adapter_key=adapter_key
        ),
        send_multitsframes_to_adapter(
            multitsframe_filtered_sinks,
            multitsframe_data_to_send,
            adapter_key=adapter_key,
        ),
        send_multiple_timeseries_to_adapter(
            timeseries_filtered_sinks, timeseries_data_to_send, adapter_key=adapter_key
        ),
        send_multiple_metadata_to_adapter(
            metadata_filtered_sinks, metadata_data_to_send, adapter_key=adapter_key
        ),
    )

    return {}
