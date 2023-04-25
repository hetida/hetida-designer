import asyncio

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.generic_rest.load_framelike import load_framelike_data
from hetdesrun.models.data_selection import FilteredSource


async def load_single_multitsframe_from_adapter(
    filtered_source: FilteredSource,
    from_timestamp: str,
    to_timestamp: str,
    adapter_key: str,
) -> pd.DataFrame:
    return await load_framelike_data(
        [filtered_source],
        additional_params=[
            ("from", from_timestamp),
            ("to", to_timestamp),
        ],
        adapter_key=adapter_key,
        endpoint="multitsframe",
    )


async def load_multitsframes_from_adapter(
    data_to_load: dict[str, FilteredSource], adapter_key: str
) -> dict[str, pd.DataFrame]:
    for filtered_source in data_to_load.values():
        if (
            not isinstance(filtered_source.filters.get("timestampFrom", None), str)
        ) or (not isinstance(filtered_source.filters.get("timestampTo", None), str)):
            raise AdapterClientWiringInvalidError(
                "MultiTSFrame data with no to/from filters."
            )
    loaded_frames = await asyncio.gather(
        *[
            load_single_multitsframe_from_adapter(
                filtered_source,
                filtered_source.filters["timestampFrom"],
                filtered_source.filters["timestampFrom"],
                adapter_key,
            )
            for filtered_source in data_to_load.values()
        ]
    )
    return dict(zip(data_to_load.keys(), loaded_frames, strict=True))
