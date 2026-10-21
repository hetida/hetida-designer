"""Validation of metadata received from generic REST adapters

Whether the metadata received via the Data-Attributes header is checked against the metadata
conventions is configured per adapter via GENERIC_REST_ADAPTER_METADATA_VALIDATION.
"""

import logging
from typing import Literal

import pandas as pd

from hetdesrun.adapters.exceptions import AdapterInputDataError
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.models.metadata_conventions import (
    MetadataConventionIssue,
    MetadataIssueSeverity,
    TimeseriesDataType,
    check_metadata_conventions,
)
from hetdesrun.webservice.config import MetadataValidationMode, get_config

logger = logging.getLogger(__name__)

# DATAFRAMEs are not covered by the metadata conventions
DATA_TYPE_BY_ENDPOINT: dict[str, TimeseriesDataType] = {
    "timeseries": "SERIES",
    "multitsframe": "MULTITSFRAME",
    "singletsframe": "SINGLETSFRAME",
}


def check_received_metadata(
    df: pd.DataFrame,
    endpoint: Literal["timeseries", "dataframe", "multitsframe", "singletsframe"],
    filtered_sources: list[FilteredSource],
) -> dict[str, list[MetadataConventionIssue]]:
    """Check the metadata received with framelike data against the metadata conventions

    For the timeseries endpoint the received metadata maps the ids of the timeseries to their
    metadata, which is checked for each requested timeseries. The other endpoints provide the
    data of a single source together with its metadata.

    Returns the found issues by source id, omitting sources without issues.
    """
    data_type = DATA_TYPE_BY_ENDPOINT.get(endpoint)
    if data_type is None:
        return {}

    if endpoint == "timeseries":
        issues_by_source_id = {
            str(filtered_source.ref_id): check_metadata_conventions(
                df.attrs.get(filtered_source.ref_id, {}), data_type
            )
            for filtered_source in filtered_sources
        }
    else:
        issues_by_source_id = {
            str(filtered_sources[0].ref_id): check_metadata_conventions(df, data_type)
        }
    return {
        source_id: issues for source_id, issues in issues_by_source_id.items() if len(issues) > 0
    }


def validate_received_metadata(
    df: pd.DataFrame,
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe", "multitsframe", "singletsframe"],
    filtered_sources: list[FilteredSource],
) -> None:
    """Validate the received metadata as configured for the adapter

    With validation mode WARN, issues are logged as warning. With mode ERROR, errors let loading
    fail with an AdapterInputDataError, while sources with only warnings are logged as warning.
    """
    mode = get_config().generic_rest_adapter_metadata_validation.get(
        adapter_key, MetadataValidationMode.OFF
    )
    if mode == MetadataValidationMode.OFF:
        return

    error_messages = []
    for source_id, issues in check_received_metadata(df, endpoint, filtered_sources).items():
        msg = (
            f"Metadata received from generic REST adapter {adapter_key} for {endpoint} source"
            f" {source_id} does not adhere to the metadata conventions. Found issues:\n"
            + "\n".join(
                f"* {issue.severity} at {issue.location or 'top level'}: {issue.message}"
                for issue in issues
            )
        )
        if mode == MetadataValidationMode.ERROR and any(
            issue.severity == MetadataIssueSeverity.ERROR for issue in issues
        ):
            error_messages.append(msg)
        else:
            logger.warning(msg)

    if len(error_messages) > 0:
        msg = "\n".join(error_messages)
        logger.info(msg)
        raise AdapterInputDataError(msg)
