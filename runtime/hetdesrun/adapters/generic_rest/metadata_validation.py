"""Validation of metadata received from generic REST adapters

Whether the metadata received via the Data-Attributes header is checked against the metadata
conventions is configured per adapter via GENERIC_REST_ADAPTER_METADATA_VALIDATION.
"""

import logging
import re
from collections.abc import Mapping
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


def _listing(items: list[str], max_items: int = 5) -> str:
    listed = ", ".join(items[:max_items])
    if len(items) > max_items:
        listed += f" and {len(items) - max_items} more"
    return listed


def summarize_issues(issues_by_source: Mapping[str, list[MetadataConventionIssue]]) -> str:
    """The issues of the sources as lines, each distinct issue listed once

    Issues which only differ in the indices of their locations, e.g. the same unknown field in
    every metric, are listed once (with [*] instead of differing indices) with the number of their
    occurrences and, for several sources, with the sources they occur in. So the issues of many
    sources or metrics do not flood the logs.
    """
    occurrences: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    for source_id, issues in issues_by_source.items():
        for issue in issues:
            key = (issue.severity, re.sub(r"\[\d+\]", "[*]", issue.location), issue.message)
            occurrences.setdefault(key, []).append((source_id, issue.location))

    lines = []
    for (severity, location_pattern, message), found in occurrences.items():
        locations = {location for _, location in found}
        location = next(iter(locations)) if len(locations) == 1 else location_pattern
        line = f"* {severity} at {location or 'top level'}: {message}"
        sources = list(dict.fromkeys(source_id for source_id, _ in found))
        times = f"{len(found)} times" if len(found) > len(sources) else ""
        if len(issues_by_source) > 1:
            line += f" ({times + ' ' if times else ''}in sources {_listing(sources)})"
        elif times:
            line += f" ({times})"
        lines.append(line)
    return "\n".join(lines)


def _not_adhering_message(
    adapter_key: str,
    endpoint: str,
    issues_by_source: Mapping[str, list[MetadataConventionIssue]],
    source_count: int,
) -> str:
    source_ids = list(issues_by_source)
    sources = (
        f"source {source_ids[0]}"
        if len(source_ids) == 1
        else f"{len(source_ids)} of {source_count} sources ({_listing(source_ids)})"
    )
    return (
        f"Metadata received from generic REST adapter {adapter_key} for {endpoint} {sources}"
        " does not adhere to the metadata conventions. Found issues:\n"
        + summarize_issues(issues_by_source)
    )


def validate_received_metadata(
    df: pd.DataFrame,
    adapter_key: str,
    endpoint: Literal["timeseries", "dataframe", "multitsframe", "singletsframe"],
    filtered_sources: list[FilteredSource],
) -> None:
    """Validate the received metadata as configured for the adapter

    With validation mode WARN, issues are logged as warning. With mode ERROR, errors let loading
    fail with an AdapterInputDataError, while sources with only warnings are logged as warning.
    The issues of all sources are summarized in one message, see summarize_issues.
    """
    mode = get_config().generic_rest_adapter_metadata_validation.get(
        adapter_key, MetadataValidationMode.OFF
    )
    if mode == MetadataValidationMode.OFF:
        return

    issues_by_source = check_received_metadata(df, endpoint, filtered_sources)
    failing = {
        source_id: issues
        for source_id, issues in issues_by_source.items()
        if mode == MetadataValidationMode.ERROR
        and any(issue.severity == MetadataIssueSeverity.ERROR for issue in issues)
    }
    warned = {
        source_id: issues
        for source_id, issues in issues_by_source.items()
        if source_id not in failing
    }
    if len(warned) > 0:
        logger.warning(_not_adhering_message(adapter_key, endpoint, warned, len(filtered_sources)))
    if len(failing) > 0:
        msg = _not_adhering_message(adapter_key, endpoint, failing, len(filtered_sources))
        logger.info(msg)
        raise AdapterInputDataError(msg)
