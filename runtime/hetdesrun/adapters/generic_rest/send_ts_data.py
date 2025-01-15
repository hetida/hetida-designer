import asyncio
import datetime

import numpy as np
import pandas as pd
import pytz
from httpx import AsyncClient

from hetdesrun.adapters.exceptions import AdapterOutputDataError
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.send_framelike import post_framelike_records
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.webservice.config import get_config


def validate_series_dtype(series: pd.Series, sink_type: ExternalType) -> None:
    """Raise appropriate exceptions if sink_type and series value dtype do not match"""

    if sink_type.endswith("(float)"):
        if pd.api.types.is_float_dtype(series):
            return
        raise AdapterOutputDataError(
            f"Expected float value dtype for series but got {str(series.dtype)}."
        )
    if sink_type.endswith("(int)"):
        if pd.api.types.is_integer_dtype(series):
            return
        raise AdapterOutputDataError(
            f"Expected int value dtype for series but got {str(series.dtype)}."
        )
    if sink_type.endswith(("(boolean)", "(bool)")):
        if pd.api.types.is_bool_dtype(series):
            return
        raise AdapterOutputDataError(
            f"Expected bool value dtype for series but got {str(series.dtype)}."
        )
    if sink_type.endswith(("(str)", "(string)")):
        if pd.api.types.is_string_dtype(series):
            return
        raise AdapterOutputDataError(
            f"Expected string value dtype for series but got {str(series.dtype)}."
        )
    if sink_type.endswith("(numeric)"):
        if pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series):
            return
        raise AdapterOutputDataError(
            f"Expected int or float value dtype for series but got {str(series.dtype)}."
        )

    raise AdapterOutputDataError(f"Sink has {sink_type} no known dtype specified for series")


def ts_to_list_of_dicts(series: pd.Series, sink_type: ExternalType) -> list[dict]:
    if not isinstance(series, pd.Series):
        raise AdapterOutputDataError(
            "Did not receive Pandas Series as expected from workflow output."
            f" Got {str(type(series))} instead."
        )

    if len(series) == 0:
        return []

    if not pd.api.types.is_datetime64_any_dtype(series.index):
        raise AdapterOutputDataError(
            "Received Pandas Series does not have DatetimeTZDtype dtype index as expected for"
            f" generic rest adapter timeseries endpoints. Got {str(series.index.dtype)} "
            "index dtype instead."
        )

    if not series.index.tz in (pytz.UTC, datetime.timezone.utc):
        raise AdapterOutputDataError(
            "Received Pandas Series index does not have UTC timezone but generic rest adapter "
            "only accepts UTC timeseries data."
            f" Got {str(series.index.dtype)} index dtype instead."
        )
    validate_series_dtype(series, sink_type)

    return (  # type: ignore
        pd.DataFrame(
            {
                "value": series.to_numpy(),
                "timestamp": pd.Series(series.index, index=series.index).apply(
                    lambda x: x.strftime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    )  # Generic Rest datetime format is yyyy-MM-ddTHH:mm:ss.SSSSSSSSSX
                    + "{:03d}".format(x.nanosecond)  # noqa: UP032
                    + "Z"  # we guaranteed UTC time zone some lines above!
                ),
            }
        )
        .replace({np.nan: None})
        .to_dict(orient="records")
    )


async def post_single_timeseries(
    series: pd.Series,
    ref_id: str,
    additional_params: list[tuple[str, str]],
    sink_type: ExternalType,
    adapter_key: str,
    client: AsyncClient,
) -> None:
    records = ts_to_list_of_dicts(series, sink_type)

    await post_framelike_records(
        records,
        attributes=series.attrs,
        ref_id=ref_id,
        additional_params=additional_params,
        adapter_key=adapter_key,
        endpoint="timeseries",
        client=client,
    )


async def post_multiple_timeseries(
    timeseries_list: list[pd.Series],
    ref_ids: list[str],
    sink_filters: list[dict[str, str]],
    sink_types: list[ExternalType],
    adapter_key: str,
) -> None:
    async with AsyncClient(
        verify=get_config().hd_adapters_verify_certs,
        timeout=get_config().external_request_timeout,
    ) as client:
        await asyncio.gather(
            *(
                post_single_timeseries(
                    series,
                    ref_id,
                    additional_params=list(filters.items()),
                    sink_type=sink_type,
                    adapter_key=adapter_key,
                    client=client,
                )
                for series, ref_id, filters, sink_type in zip(
                    timeseries_list, ref_ids, sink_filters, sink_types, strict=True
                )
            )
        )


async def send_multiple_timeseries_to_adapter(
    filtered_sinks: dict[str, FilteredSink],
    data_to_send: dict[str, pd.Series],
    adapter_key: str,
) -> None:
    keys = filtered_sinks.keys()
    ref_ids = [str(filtered_sinks[key].ref_id) for key in keys]
    sink_filters = [filtered_sinks[key].filters for key in keys]
    sink_types = [ExternalType(filtered_sinks[key].type) for key in keys]
    series_list = [data_to_send[key] for key in keys]

    await post_multiple_timeseries(
        series_list, ref_ids, sink_filters, sink_types, adapter_key=adapter_key
    )
