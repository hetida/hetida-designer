import logging
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from hetdesrun.adapters.exceptions import (
    AdapterClientWiringInvalidError,
    AdapterHandlingException,
)
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_framelike import load_framelike_data
from hetdesrun.models.data_selection import FilteredSource

logger = logging.getLogger(__name__)


async def load_ts_data_from_adapter(
    filtered_sources: List[FilteredSource],
    from_timestamp: str,
    to_timestamp: str,
    adapter_key: str,
) -> pd.DataFrame:
    """Load data from generic rest adapter timeseries endpoint

    filtered_sources are expected to all have the exact same type which must be a
    timeseries(...) variant.

    Data is returned as a DataFrame with a timestamp column,
    a "value" column with automatically inferred dtype
    and a timeseriesId column with dtype str.

    This uses request with stream=True in combination with the raw response as file-like together
    with Pandas read_json class method to get some minor performance out of the streaming.

    It therefore currently isn't async.
    """

    return await load_framelike_data(
        filtered_sources=filtered_sources,
        additional_params=[("from", from_timestamp), ("to", to_timestamp)],
        adapter_key=adapter_key,
        endpoint="timeseries",
    )


def extract_one_channel_series_from_loaded_data(
    df: pd.DataFrame, ts_id: str
) -> pd.Series:
    try:
        extracted_df = df[df["timeseriesId"] == ts_id].copy()
        extracted_df.index = extracted_df["timestamp"]
        extracted_series = extracted_df["value"].sort_index()
    except KeyError as e:
        msg = (
            f"Missing keys in received timeseries records. Got columns {str(df.columns)}"
            f" with dataframe of shape {str(df.shape)}:\n{str(df)}"
        )
        logger.info(msg)
        raise AdapterHandlingException(msg) from e

    extracted_series.name = ts_id

    return extracted_series


async def load_grouped_timeseries_data_together(
    data_to_load: Dict[str, FilteredSource], adapter_key: str
) -> Dict[str, pd.Series]:
    """Reorganize query information by timestamp pairs and load timeseries data

    Generic Rest Adapter allows to query for multiple timeseries in one request but then only with
    one timestamp filter pair and same (requested) value type for all those timeseries.

    This function expects data refs of the timeseries type,
    groups them together if they have same filter timestamp pairs and same value type,
    loads each such group in one request
    and returns all results gathered.
    """
    loaded_data = {}

    # group by occuring timestamp pairs
    group_by_timestamp_pair: Dict[
        Tuple[str, str, ExternalType],
        Dict[str, FilteredSource],
    ] = defaultdict(dict)

    for filtered_source in data_to_load.values():
        if (
            not isinstance(filtered_source.filters.get("timestampFrom", None), str)
        ) or (not isinstance(filtered_source.filters.get("timestampTo", None), str)):
            raise AdapterClientWiringInvalidError(
                "Timeseries data with no to/from filters."
            )

    for key, filtered_source in data_to_load.items():
        group_by_timestamp_pair[
            (
                filtered_source.filters["timestampFrom"],
                filtered_source.filters["timestampTo"],
                ExternalType(filtered_source.type),
            )
        ][key] = filtered_source

    # load each group together:
    for (group_tuple, grouped_source_dict) in group_by_timestamp_pair.items():
        loaded_ts_data_from_adapter = await load_ts_data_from_adapter(
            list(grouped_source_dict.values()),
            group_tuple[0],
            group_tuple[1],
            adapter_key=adapter_key,
        )

        loaded_data.update(
            {
                key: extract_one_channel_series_from_loaded_data(
                    loaded_ts_data_from_adapter,
                    filtered_source.ref_id,  # type: ignore
                )
                for key, filtered_source in grouped_source_dict.items()
            }
        )

        try:
            received_ids = loaded_ts_data_from_adapter["timeseriesId"].unique()
        except KeyError as e:
            msg = (
                f"Missing keys in received timeseries records."
                f" Got columns {str(loaded_ts_data_from_adapter.columns)}"
                f" with dataframe of shape {str(loaded_ts_data_from_adapter.shape)}:\n"
                f"{str(loaded_ts_data_from_adapter)}"
            )
            logger.info(msg)
            raise AdapterHandlingException(msg) from e

        queried_ids = [fs.ref_id for fs in grouped_source_dict.values()]

        if not np.isin(received_ids, np.array(queried_ids)).all():
            msg = (
                f"Found timeseries ids in received data that were not queried."
                f" Received timeseriesId unique values were:\n{str(received_ids.tolist())}"
                f" \nQueried ids were:\n{str(queried_ids)}."
                "\nThis unassignable data will be discarded. This indicates an error in the adapter"
                f" implementation of the adapter {str(adapter_key)}!"
            )
            logger.warning(msg)

    return loaded_data
