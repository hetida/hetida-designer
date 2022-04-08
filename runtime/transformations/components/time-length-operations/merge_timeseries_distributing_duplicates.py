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

from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType

import pandas as pd
import numpy as np


def cumsum_resetting_at_nan(orig):
    """Compute a cumsum but resetting at every nan value"""
    cumsum = orig.cumsum().fillna(method="ffill")

    # take cumsum at nan positions and then diff to last
    # position before with nan value. This gives the
    # value added to cumsum "in-between".
    # Edge case: After the first portion the diff is null, here we can
    # simply fill with the cumsum value itself (".fillna(cumsum)")
    # The negative of this can be used adapt the cumsum.
    reset = -(cumsum[orig.isnull()].diff().fillna(cumsum))

    result = orig.where(orig.notnull(), reset).cumsum()

    return result.fillna(0)


def dupl_count_at_duplicated_positions(orig, dupl_counts):
    """A series where the total number of duplicates in a sequence is written at every duplicate position"""
    last_duplicated_position = orig.duplicated() & (
        ~orig.duplicated().shift(-1).fillna(False)
    )
    return dupl_counts.where(
        last_duplicated_position | (dupl_counts == 0), np.nan
    ).backfill()


def dupl_delta_to_next(orig):
    """Delta to next different timestamp at every position"""
    last_duplicated_position = orig.duplicated() & (
        ~orig.duplicated().shift(-1).fillna(False)
    )
    timestamps_after = (
        (orig.shift(-1))
        .where(last_duplicated_position, orig.where(~orig.duplicated()))
        .bfill()
    )
    delta_to = (timestamps_after - orig).fillna(pd.Timedelta(0))
    return delta_to


def distribute_duplicated_timestamps(timestamp_series, max_distribution_delta: str):
    """distribute duplicated timestamps to get unique timestamps

    This is useful if you want to "merge" two timeseries without throwing
    away values or aggregating and if you need unique timestamps in the end result.

    It moves duplicate timestamps a bit into the future to archieve this.


    timestamp_series: series with timestamp values (containing duplicates).
        Should be sorted by these timestamp values. Will be sorted here nevertheless.
        Index is ignored.

    max_distribution_delta (str for pd.Timedelta): If the next timestamp after some duplicated timestamps
        is further away than this delta, the duplicated timestamps will be distributed
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
    """Merges multiple timeseries into one, deduplicating timestamps by moving them into the future a bit

    timeseries_df should be sorted
    """
    timeseries_df.sort_values("timestamp", inplace=True)

    new_timestamps = distribute_duplicated_timestamps(
        timeseries_df["timestamp"], max_distribution_delta
    )

    return pd.Series(timeseries_df["value"].values, index=new_timestamps, name=name)


# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={
        "timeseries_df": DataType.DataFrame,
        "max_distribution_delta": DataType.String,
        "new_name": DataType.String,
    },
    outputs={"timeseries": DataType.Series},
    component_name="Merge timeseries deduplicating timestamps",
    description="Combine multiple timeseries from a timeseries dataframe into one, avoiding duplicate timestamps.",
    category="Time length operations",
    uuid="b1dba357-b6d5-43cd-ac3e-7b6cd829be37",
    group_id="79de1ec7-b629-4360-a5e2-4eba19e60bd0",
    tag="1.0.0",
)
def main(*, timeseries_df, max_distribution_delta, new_name):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    return {
        "timeseries": merge_with_deduplicated_timestamps(
            timeseries_df, max_distribution_delta, new_name
        )
    }
