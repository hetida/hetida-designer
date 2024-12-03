import asyncio
import datetime

import numpy as np
import pandas as pd
import pytz
from httpx import AsyncClient

from hetdesrun.adapters.exceptions import AdapterOutputDataError
from hetdesrun.adapters.generic_rest.send_framelike import post_framelike_records
from hetdesrun.models.data_selection import FilteredSink
from hetdesrun.webservice.config import get_config


def multitsframe_to_list_of_dicts(df: pd.DataFrame) -> list[dict]:
    """Prepares serialization by converting rows into json-serializable dicts

    * validates form of the dataframe (columns and missing values)
    * np.nan -> None
    * datetimes are enforced to be UTC and are converted to zulu-format strings

    Note: The given pandas.DataFrame is not modified. We cannot use
    PydanticMultiTimeseriesPandasDataFrame here since this would mutate
    the df object.

    However, the applied validations are mostly the same.
    """

    if not isinstance(df, pd.DataFrame):
        raise AdapterOutputDataError(
            "Did not receive Pandas DataFrame as expected from workflow output."
            f" Got {str(type(df))} instead."
        )

    if len(df) == 0:
        return []

    if len(df.columns) < 3:
        raise AdapterOutputDataError(
            "MultiTSFrame requires at least 3 columns: metric, timestamp"
            f" and at least one additional columns. Only found { {*df.columns} }"
        )

    if not ({"metric", "timestamp"}.issubset(set(df.columns))):
        raise AdapterOutputDataError(
            f"The column names { {*df.columns} } don't contain required columns"
            ' "timestamp" and "metric" for a MultiTSFrame.'
        )

    if df["metric"].isna().any():
        raise AdapterOutputDataError(
            "Received Pandas Dataframe with null values in the column 'metric'."
        )

    if df["timestamp"].isna().any():
        raise AdapterOutputDataError(
            "Received Pandas Dataframe with null values in the column 'timestamp'."
        )

    if not isinstance(df["timestamp"].dtype, pd.DatetimeTZDtype):
        raise AdapterOutputDataError(
            "Column 'timestamp' of the received Pandas Dataframe does not have DatetimeTZDtype "
            "dtype index as expected for generic rest adapter multitsframe endpoints. "
            f'Got {str(df["timestamp"].dtype)} index dtype instead.'
        )

    if not df["timestamp"].dt.tz in (pytz.UTC, datetime.timezone.utc):
        raise AdapterOutputDataError(
            "Column 'timestamp' of the received Pandas Dataframe does not have UTC timezone "
            "but generic rest adapter only accepts UTC timeseries data. "
            f'Got {str(df["timestamp"].dt.tz)} timezone instead.'
        )

    new_df = df.replace({np.nan: None})
    new_df["timestamp"] = new_df["timestamp"].apply(
        lambda x: x.strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )  # Generic Rest datetime format is yyyy-MM-ddTHH:mm:ss.SSSSSSSSSX
        + "{:03d}".format(x.nanosecond)  # noqa: UP032
        + "Z"  # we guaranteed UTC time zone some lines above!
    )
    return new_df.to_dict(orient="records")  # type: ignore


async def post_multitsframe(
    df: pd.DataFrame,
    ref_id: str,
    additional_params: list[tuple[str, str]],
    adapter_key: str,
    client: AsyncClient,
) -> None:
    records = multitsframe_to_list_of_dicts(df)

    await post_framelike_records(
        records,
        attributes=df.attrs,
        ref_id=ref_id,
        additional_params=additional_params,
        adapter_key=adapter_key,
        endpoint="multitsframe",
        client=client,
    )


async def post_multitsframes(
    dfs: list[pd.DataFrame],
    ref_ids: list[str],
    sink_filters: list[dict[str, str]],
    adapter_key: str,
) -> None:
    async with AsyncClient(
        verify=get_config().hd_adapters_verify_certs,
        timeout=get_config().external_request_timeout,
    ) as client:
        await asyncio.gather(
            *(
                post_multitsframe(
                    df,
                    ref_id,
                    additional_params=list(filters.items()),
                    adapter_key=adapter_key,
                    client=client,
                )
                for df, ref_id, filters in zip(dfs, ref_ids, sink_filters, strict=True)
            )
        )


async def send_multitsframes_to_adapter(
    filtered_sinks: dict[str, FilteredSink],
    data_to_send: dict[str, pd.DataFrame],
    adapter_key: str,
) -> None:
    keys = filtered_sinks.keys()
    ref_ids: list[str] = [str(filtered_sinks[key].ref_id) for key in keys]
    sink_filters: list[dict[str, str]] = [filtered_sinks[key].filters for key in keys]
    dfs = [data_to_send[key] for key in keys]

    await post_multitsframes(
        dfs, ref_ids=ref_ids, sink_filters=sink_filters, adapter_key=adapter_key
    )
