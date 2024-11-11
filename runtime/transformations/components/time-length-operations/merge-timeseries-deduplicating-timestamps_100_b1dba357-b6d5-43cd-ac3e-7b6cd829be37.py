"""Merge timeseries deduplicating timestamps

# Merge timeseries deduplicating timestamps

This components merges all timeseries in a multiple timeseries dataframe
of the form provided by the Timeseries Dataframe component. Thereby it avoids
duplicates by moving duplicate timestamps into the future, distributing them
evenly with respect to the next differing timestamp, bounded by a maximum timedelta
providable as paramter.

This component may be useful if
* a signal is measured by multiple sensors
* which may lead to duplicate timestamps (but possibly different values)
* you want to keep all values (e.g. to detect outliers) and methods like
  mean / median aggregation are not suitable
* moving duplicate timestamps into the future does not affect your analysis
  too much.


"""

import numpy as np
import pandas as pd


def cumsum_resetting_at_nan(orig):
    """Compute a cumsum but resetting at every nan value"""
    cumsum = orig.cumsum().fillna(method="ffill")

    # take cumsum at nan positions and then diff to last
    # position before with nan value. This gives the
    # value added to cumsum "in-between".
    # Edge case: After the first portion the diff is null, here we can
    # simply fill with the cumsum value itself (".fillna(cumsum)")
    # The negative of this can be used adapt the cumsum.
    reset = -(cumsum[orig.isna()].diff().fillna(cumsum))

    result = orig.where(orig.notna(), reset).cumsum()

    return result.fillna(0)


def dupl_count_at_duplicated_positions(orig, dupl_counts):
    """Count duplicates

    Return a series where the total number of duplicates in a sequence is written at every duplicate
    position.
    """
    last_duplicated_position = orig.duplicated() & (~orig.duplicated().shift(-1).fillna(False))
    return dupl_counts.where(last_duplicated_position | (dupl_counts == 0), np.nan).backfill()


def dupl_delta_to_next(orig):
    """Delta to next different timestamp at every position"""
    last_duplicated_position = orig.duplicated() & (~orig.duplicated().shift(-1).fillna(False))
    timestamps_after = (
        (orig.shift(-1)).where(last_duplicated_position, orig.where(~orig.duplicated())).bfill()
    )
    delta_to = (timestamps_after - orig).fillna(pd.Timedelta(0))
    return delta_to


def distribute_duplicated_timestamps(timestamp_series, max_distribution_delta: str):
    """Distribute duplicated timestamps to get unique timestamps

    This is useful if you want to "merge" two timeseries without throwing
    away values or aggregating and if you need unique timestamps in the end result.

    It moves duplicate timestamps a bit into the future to archieve this.


    timestamp_series: series with timestamp values (containing duplicates).
        Should be sorted by these timestamp values. Will be sorted here nevertheless.
        Index is ignored.

    max_distribution_delta (str for pd.Timedelta): If the next timestamp after some duplicated
        timestamps is further away than this delta, the duplicated timestamps will be distributed
        uniformly in the time interval starting at the duplicated value and ending after
        this delta beginning from the duplicated value and continuing in
            1/(number of duplicates +1) * max_distribution_delta
        steps. If the next timestamp after some duplicated timestamps
        is nearer than this delta, the delta to this next timestamp is used instead of
        max_distribution_delta.

        Examples: "1h", "5min", "1h30min"
    """

    max_dist_delta_timedelta = pd.Timedelta(max_distribution_delta)

    working_timestamp_series = timestamp_series.sort_values()

    # mark as True from second occurences onwards:
    duplicates_marked = working_timestamp_series.duplicated()

    duplicates_true_other_nan = duplicates_marked.where(duplicates_marked, np.nan)

    factors_at_duplicate_positions = cumsum_resetting_at_nan(duplicates_true_other_nan)

    dupl_count_at_duplicate_positions = dupl_count_at_duplicated_positions(
        working_timestamp_series, factors_at_duplicate_positions
    )

    delta_to = dupl_delta_to_next(working_timestamp_series)

    selected_series = pd.Series(max_dist_delta_timedelta, index=delta_to.index)
    return (
        working_timestamp_series
        + factors_at_duplicate_positions
        * 1
        / (dupl_count_at_duplicate_positions + 1)
        * pd.DataFrame(
            [
                delta_to.where(delta_to > pd.Timedelta(0), selected_series),
                selected_series,
            ]
        ).min()
    )


def merge_with_deduplicated_timestamps(
    timeseries_df, max_distribution_delta: str, name="merged_timeseries"
):
    """Merge multiple timeseries into one

    Timestamps ar deduplicated by moving them into the future a bit.
    """
    sorted_timeseries_df = timeseries_df.sort_values("timestamp")

    new_timestamps = distribute_duplicated_timestamps(
        sorted_timeseries_df["timestamp"], max_distribution_delta
    )

    return pd.Series(sorted_timeseries_df["value"].values, index=new_timestamps, name=name)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "timeseries_df": {"data_type": "DATAFRAME"},
        "max_distribution_delta": {"data_type": "STRING"},
        "new_name": {"data_type": "STRING"},
    },
    "outputs": {
        "timeseries": {"data_type": "SERIES"},
    },
    "name": "Merge timeseries deduplicating timestamps",
    "category": "Time length operations",
    "description": "Combine multiple timeseries from a timeseries dataframe into one, avoiding duplicate timestamps.",  # noqa: E501
    "version_tag": "1.0.0",
    "id": "b1dba357-b6d5-43cd-ac3e-7b6cd829be37",
    "revision_group_id": "79de1ec7-b629-4360-a5e2-4eba19e60bd0",
    "state": "RELEASED",
    "released_timestamp": "2023-09-25T09:57:52.580730+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, timeseries_df, max_distribution_delta, new_name):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "timeseries": merge_with_deduplicated_timestamps(
            timeseries_df, max_distribution_delta, new_name
        )
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {}
RELEASE_WIRING = {}
