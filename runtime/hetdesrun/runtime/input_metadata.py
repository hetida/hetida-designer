"""Attaching the metadata of workflow inputs as model

The metadata of every SERIES, SINGLETSFRAME and MULTITSFRAME workflow input wired to an adapter,
including manual input via direct provisioning, is parsed once and attached to the data as
immutable model (see hdhelpers.metadata.attached), if it adheres to the metadata conventions.

How metadata not adhering to the conventions is handled is configured per adapter via
ADAPTER_METADATA_VALIDATION: OFF (default) leaves it as it is silently, WARN logs the found issues
and ERROR lets the execution fail on errors. With WARN and ERROR, missing metadata is an issue as
well. Otherwise metadata that cannot be parsed would just be missing for the components, without
any hint why.
"""

import logging
import re
from collections.abc import Mapping
from typing import Any

import pandas as pd
from hdhelpers.metadata.attached import CONVENTION_KEYS, META_KEY, attach_metadata
from hdhelpers.metadata.conventions import (
    MetadataConventionIssue,
    MetadataIssueSeverity,
    TimeseriesDataType,
    check_metadata_conventions,
)

from hdutils import DataType
from hetdesrun.adapters.exceptions import AdapterInputDataError
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.webservice.config import MetadataValidationMode, get_config

logger = logging.getLogger(__name__)

# DATAFRAMEs are not covered by the metadata conventions
TIMESERIES_DATA_TYPES: dict[DataType, TimeseriesDataType] = {
    DataType.Series: "SERIES",
    DataType.SingleTSFrame: "SINGLETSFRAME",
    DataType.MultiTSFrame: "MULTITSFRAME",
}


def adapter_key_of(input_wiring: InputWiring) -> str:
    """The key of the adapter of an input wiring, as used in ADAPTER_METADATA_VALIDATION"""
    # 1 is the legacy key of the direct provisioning adapter
    if input_wiring.adapter_id == 1:
        return "direct_provisioning"
    return str(input_wiring.adapter_id)


def validation_mode(adapter_key: str) -> MetadataValidationMode:
    return get_config().adapter_metadata_validation.get(adapter_key, MetadataValidationMode.OFF)


def convention_issues(
    obj: pd.Series | pd.DataFrame, data_type: TimeseriesDataType
) -> list[MetadataConventionIssue]:
    """The issues of the metadata of obj, also checked against its data

    Other top-level keys of attrs than those of the conventions are not reported as unknown
    fields: attrs may contain other information, which stays as it is when attaching.
    """
    other_keys = {str(key) for key in obj.attrs if key not in CONVENTION_KEYS | {META_KEY}}
    return [
        issue
        for issue in check_metadata_conventions(obj, data_type)
        if issue.location not in other_keys
    ]


def _listing(items: list[str], max_items: int = 5) -> str:
    listed = ", ".join(items[:max_items])
    if len(items) > max_items:
        listed += f" and {len(items) - max_items} more"
    return listed


def summarize_issues(issues_by_input: Mapping[str, list[MetadataConventionIssue]]) -> str:
    """The issues of the inputs as lines, each distinct issue listed once

    Issues which only differ in the indices of their locations, e.g. the same unknown field in
    every metric, are listed once (with [*] instead of differing indices) with the number of their
    occurrences and, for several inputs, with the inputs they occur in. So the issues of many
    inputs or metrics do not flood the logs.
    """
    occurrences: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    for input_name, issues in issues_by_input.items():
        for issue in issues:
            key = (issue.severity, re.sub(r"\[\d+\]", "[*]", issue.location), issue.message)
            occurrences.setdefault(key, []).append((input_name, issue.location))

    lines = []
    for (severity, location_pattern, message), found in occurrences.items():
        locations = {location for _, location in found}
        location = next(iter(locations)) if len(locations) == 1 else location_pattern
        line = f"* {severity} at {location or 'top level'}: {message}"
        input_names = list(dict.fromkeys(input_name for input_name, _ in found))
        times = f"{len(found)} times" if len(found) > len(input_names) else ""
        if len(issues_by_input) > 1:
            line += f" ({times + ' ' if times else ''}in inputs {_listing(input_names)})"
        elif times:
            line += f" ({times})"
        lines.append(line)
    return "\n".join(lines)


def _not_adhering_message(
    adapter_key: str,
    issues_by_input: Mapping[str, list[MetadataConventionIssue]],
    input_wirings_by_name: Mapping[str, InputWiring],
) -> str:
    inputs = ", ".join(
        f"{input_name} (source {input_wirings_by_name[input_name].ref_id})"
        if adapter_key != "direct_provisioning"
        else input_name
        for input_name in issues_by_input
    )
    return (
        f"Metadata received from adapter {adapter_key} for workflow"
        f" input{'s' if len(issues_by_input) > 1 else ''} {inputs} does not adhere to the"
        " metadata conventions. Found issues:\n" + summarize_issues(issues_by_input)
    )


def _check_inputs_of_adapter(
    adapter_key: str,
    objs_by_input: Mapping[str, tuple[pd.Series | pd.DataFrame, TimeseriesDataType]],
    input_wirings_by_name: Mapping[str, InputWiring],
) -> None:
    """Check the metadata of the inputs of an adapter as configured for it

    With validation mode WARN, issues are logged as warning. With mode ERROR, errors let the
    execution fail with an AdapterInputDataError, while inputs with only warnings are logged as
    warning. Inputs without metadata are checked as well, i.e. the missing required fields are
    errors. The issues of all inputs are summarized in one message, see summarize_issues.
    """
    mode = validation_mode(adapter_key)
    if mode == MetadataValidationMode.OFF:
        return

    issues_by_input = {
        input_name: issues
        for input_name, (obj, data_type) in objs_by_input.items()
        if len(issues := convention_issues(obj, data_type)) > 0
    }
    failing = {
        input_name: issues
        for input_name, issues in issues_by_input.items()
        if mode == MetadataValidationMode.ERROR
        and any(issue.severity == MetadataIssueSeverity.ERROR for issue in issues)
    }
    warned = {
        input_name: issues
        for input_name, issues in issues_by_input.items()
        if input_name not in failing
    }
    if len(warned) > 0:
        logger.warning(_not_adhering_message(adapter_key, warned, input_wirings_by_name))
    if len(failing) > 0:
        msg = _not_adhering_message(adapter_key, failing, input_wirings_by_name)
        logger.info(msg)
        raise AdapterInputDataError(msg)


def attach_input_metadata(
    parsed_inputs: Mapping[str, Any],
    workflow_wiring: WorkflowWiring,
    input_types: Mapping[str | None, DataType],
) -> None:
    """Attach the metadata of the parsed workflow inputs as model, checked as configured

    parsed_inputs are the parsed values of the workflow inputs by name, i.e. the objects the
    components receive. Their attrs are changed in place. Inputs not wired to an adapter, e.g.
    those using their default value, and inputs of other data types are skipped.

    Raises an AdapterInputDataError if the metadata of an input of an adapter with validation
    mode ERROR has errors. Then no metadata is attached.
    """
    input_wirings_by_name = {
        input_wiring.workflow_input_name: input_wiring
        for input_wiring in workflow_wiring.input_wirings
        if input_wiring.use_default_value is False
    }
    objs_by_input_by_adapter: dict[
        str, dict[str, tuple[pd.Series | pd.DataFrame, TimeseriesDataType]]
    ] = {}
    for input_name, input_wiring in input_wirings_by_name.items():
        obj = parsed_inputs.get(input_name)
        input_type = input_types.get(input_name)
        data_type = TIMESERIES_DATA_TYPES.get(input_type) if input_type is not None else None
        if data_type is None or not isinstance(obj, pd.Series | pd.DataFrame):
            continue
        objs_by_input_by_adapter.setdefault(adapter_key_of(input_wiring), {})[input_name] = (
            obj,
            data_type,
        )

    for adapter_key, objs_by_input in objs_by_input_by_adapter.items():
        _check_inputs_of_adapter(adapter_key, objs_by_input, input_wirings_by_name)

    for objs_by_input in objs_by_input_by_adapter.values():
        for obj, data_type in objs_by_input.values():
            attach_metadata(obj, data_type)
