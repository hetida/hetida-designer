"""Helper functions for metadata extraction

Thin wrappers over the functions of hdhelpers.metadata, kept for component code importing them
from here. New code should use hdhelpers.metadata directly, e.g. read_metadata.

They access metadata following the hetida designer metadata conventions, also if attached to the
data as model, as the runtime does for workflow inputs (see hdhelpers.metadata.attached), and
resolve the fallbacks of the conventions. Metadata not following the conventions, including older
or simpler structures, gives no information. Fields (e.g. of get_metric_info) are names or dotted
paths like "inherited.site"; glom specs are not supported anymore.
"""

from collections import defaultdict
from typing import Any

import pandas as pd
from hdhelpers.metadata import (
    get_display_names,
    get_measurements,
    get_metric_info,
    get_names,
    get_series_display_name,
    get_series_info,
    get_series_measurement,
    get_series_name,
    get_series_short_display_name,
    get_series_unit,
    get_short_display_names,
    get_singlets_display_names,
    get_singlets_info,
    get_singlets_measurements,
    get_singlets_metric_info,
    get_singlets_names,
    get_singlets_short_display_names,
    get_singlets_units,
    get_units,
    read_metadata,
)


def get_value_dimension_info(
    data: pd.DataFrame | pd.Series, value_dim_info: str
) -> defaultdict[str, defaultdict[str, Any]]:
    """The value of a field of each value dimension of each metric

    Returns the values as result[metric_id][column], None if unavailable. The data type of
    metadata not attached as model is inferred from data (see read_metadata).
    """
    meta = read_metadata(data)
    infos = {} if meta is None else meta.value_dimension_infos(value_dim_info)
    return defaultdict(
        lambda: defaultdict(lambda: None),
        {metric: defaultdict(lambda: None, info) for metric, info in infos.items()},
    )


__all__ = [
    "get_display_names",
    "get_measurements",
    "get_metric_info",
    "get_names",
    "get_series_display_name",
    "get_series_info",
    "get_series_measurement",
    "get_series_name",
    "get_series_short_display_name",
    "get_series_unit",
    "get_short_display_names",
    "get_singlets_display_names",
    "get_singlets_info",
    "get_singlets_measurements",
    "get_singlets_metric_info",
    "get_singlets_names",
    "get_singlets_short_display_names",
    "get_singlets_units",
    "get_units",
    "get_value_dimension_info",
]
