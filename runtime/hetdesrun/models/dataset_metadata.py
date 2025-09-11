from datetime import datetime
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ValidationError, model_validator

IntervalType = Literal["closed", "left_closed", "right_closed", "open", "left_open", "right_open"]


class DatasetMetadata(BaseModel):
    # Whether ref dataset consists of discrete datapoints
    ref_dataset_discrete: bool = False

    # Ref interval
    ref_interval_start_timestamp: datetime | None = None
    ref_interval_end_timestamp: datetime | None = None
    ref_interval_type: IntervalType | None = "closed"

    # Metric + frequency
    ref_metric: str | None = None
    ref_data_frequency: str | None = None
    ref_data_frequency_offset: str | None = None

    # Invalidation interval
    invalidation_interval_start: datetime | None = None
    invalidation_interval_end: datetime | None = None
    invalidation_interval_type: IntervalType | None = "closed"

    # Invalidation flags
    invalidate_dataset: bool = True
    delete_invalidated: bool | None = None
    invalidation_timestamp: datetime | None = None
    only_invalidate: bool = False
    new_data_invalidation_date: datetime | None = None

    @model_validator(mode="after")
    def validate_constraints(self) -> "DatasetMetadata":
        if self.only_invalidate and not self.invalidate_dataset:
            raise ValueError("only_invalidate can only be true if invalidate_dataset is also true.")

        # Check ref interval validity
        if (self.ref_interval_start_timestamp is None) ^ (self.ref_interval_end_timestamp is None):
            raise ValueError(
                "ref_interval_start_timestamp and ref_interval_end_timestamp must be set together."
            )

        if (
            self.ref_interval_start_timestamp and self.ref_interval_end_timestamp
        ) and self.ref_interval_type is None:
            raise ValueError(
                "ref_interval_type must be set "
                "if ref_interval_start_timestamp or ref_interval_end_timestamp is set."
            )

        # Check invalidation interval validity
        if (self.invalidation_interval_start is None) ^ (self.invalidation_interval_end is None):
            raise ValueError(
                "invalidation_interval_start and invalidation_interval_end must be set together."
            )

        if (
            self.invalidation_interval_start or self.invalidation_interval_end
        ) and self.invalidation_interval_type is None:
            raise ValueError(
                "invalidation_interval_type must be set "
                "if invalidation_interval_start or invalidation_interval_end is set."
            )

        return self


def get_dataset_metadata(df: pd.DataFrame) -> DatasetMetadata:
    """Extract and validate dataset_metadata from DataFrame.attrs."""
    dataset_metadata = df.attrs.get("dataset_metadata", {})
    try:
        return DatasetMetadata(**dataset_metadata)
    except ValidationError as e:
        raise ValueError(f"Invalid dataset_metadata in DataFrame.attrs: {e}") from e
