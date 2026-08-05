import asyncio

import pandas as pd
from dtexp import DtexpParsingError

from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.adapters.generic_rest.load_framelike import load_framelike_data
from hetdesrun.dt_utils import resolve_interval
from hetdesrun.models.data_selection import FilteredSource


async def load_single_singletsframe_from_adapter(
    filtered_source: FilteredSource,
    adapter_key: str,
) -> pd.DataFrame:
    return await load_framelike_data(
        [filtered_source],
        additional_params=list(filtered_source.filters.items()),
        adapter_key=adapter_key,
        endpoint="singletsframe",
    )


async def load_singletsframes_from_adapter(
    data_to_load: dict[str, FilteredSource], adapter_key: str
) -> dict[str, pd.DataFrame]:
    for filtered_source in data_to_load.values():
        start_expr = filtered_source.filters.pop("timestampFrom", None)
        end_expr = filtered_source.filters.pop("timestampTo", None)

        try:
            start, end = resolve_interval(start_expr, end_expr)
        except (ValueError, DtexpParsingError) as e:
            raise AdapterClientWiringInvalidError(
                "SingleTSFrame data could not resolve to/from filters."
            ) from e

        filtered_source.filters["from"] = start.isoformat()
        filtered_source.filters["to"] = end.isoformat()

    loaded_frames = await asyncio.gather(
        *[
            load_single_singletsframe_from_adapter(
                filtered_source,
                adapter_key,
            )
            for filtered_source in data_to_load.values()
        ]
    )
    return dict(zip(data_to_load.keys(), loaded_frames, strict=True))
