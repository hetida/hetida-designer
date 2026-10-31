"""Checking metadata against the metadata conventions via the backend endpoint

The metadata conventions for the metadata (attrs) of SERIES, SINGLETSFRAME and MULTITSFRAME
objects are specified by the models in hdhelpers.metadata.conventions, one model per data type.
See the user guide page on attached metadata for an introduction.

This module contains the parts of the check endpoint: its request body in the wrapped format of
the direct provisioning adapter and its result. The request body references the models of the
conventions, so that they occur as JSON Schemas in the openapi.json of the backend. Third party
projects, e.g. adapters providing or receiving such metadata, can validate against them.
"""

from typing import Annotated, Any, Literal

from hdhelpers.metadata.conventions import (
    MetadataConventionIssue,
    MetadataIssueSeverity,
    MultiTSFrameMetadata,
    SeriesMetadata,
    SingleTSFrameMetadata,
    TimeseriesDataType,
    check_metadata_conventions,
)
from pydantic import BaseModel, ConfigDict, Field, PlainValidator, ValidationError

from hdutils import parse_value

# Documented by the schemas of the data types, but not validated when parsing requests, since
# violations are reported as issues of the check instead.
UncheckedTimeseriesMetadata = Annotated[
    Any,
    PlainValidator(
        lambda metadata: metadata,
        json_schema_input_type=SeriesMetadata | SingleTSFrameMetadata | MultiTSFrameMetadata,
    ),
]


class WrappedTimeseriesData(BaseModel):
    """SERIES, SINGLETSFRAME or MULTITSFRAME with metadata in the wrapped format

    This is the wrapped format of the direct provisioning adapter, except that __data__ may be
    omitted to check only the metadata.
    """

    # detect misspelled fields, which would otherwise be ignored
    model_config = ConfigDict(extra="forbid")

    hd_wrapped_data_object__: Literal["SERIES", "DATAFRAME"] = Field(
        ...,
        alias="__hd_wrapped_data_object__",
        description='"SERIES" for a SERIES, "DATAFRAME" for a SINGLETSFRAME or MULTITSFRAME',
    )
    metadata__: UncheckedTimeseriesMetadata = Field(
        ...,
        alias="__metadata__",
        description="The metadata to check, following the schema of the data type",
    )
    data__: dict | list | None = Field(
        None,
        alias="__data__",
        description="The data as for the direct provisioning adapter. If omitted, only the"
        " metadata is checked.",
    )
    data_parsing_options__: dict[str, Any] = Field(
        {},
        alias="__data_parsing_options__",
        description='Additional options for parsing the data, e.g. {"orient": "split"}',
    )


class MetadataCheckResult(BaseModel):
    """Result of checking metadata against the metadata conventions"""

    valid: bool = Field(
        ..., description="Whether no errors were found. There may be warnings nevertheless."
    )
    issues: list[MetadataConventionIssue]


def check_wrapped_timeseries_data(
    data_type: TimeseriesDataType, wrapped_data: WrappedTimeseriesData
) -> MetadataCheckResult:
    """Check wrapped metadata and optionally data against the metadata conventions

    The data is parsed like a direct provisioning input of the data type. The locations of the
    issues refer to the wrapped data, e.g. __metadata__.metrics[0] or __data__ if the data cannot
    be parsed.
    """
    expected_wrapped_data_object = "SERIES" if data_type == "SERIES" else "DATAFRAME"
    if wrapped_data.hd_wrapped_data_object__ != expected_wrapped_data_object:
        raise ValueError(
            f'__hd_wrapped_data_object__ must be "{expected_wrapped_data_object}" for a'
            f" {data_type}, got {wrapped_data.hd_wrapped_data_object__}."
        )

    metadata = wrapped_data.metadata__
    checked_obj = metadata
    data_issues = []
    if wrapped_data.data__ is not None:
        # The metadata is attached after parsing, since parsing would silently treat the whole
        # wrapped data as unwrapped data if the metadata is not a dict.
        try:
            parsed_data = parse_value(
                {
                    "__hd_wrapped_data_object__": expected_wrapped_data_object,
                    "__metadata__": {},
                    "__data__": wrapped_data.data__,
                    "__data_parsing_options__": wrapped_data.data_parsing_options__,
                },
                data_type,
                False,
            )
        except Exception as e:  # noqa: BLE001  # any parsing failure is a finding of the check
            message = (
                "; ".join(error["msg"].removeprefix("Value error, ") for error in e.errors())
                if isinstance(e, ValidationError)
                else str(e)
            )
            data_issues.append(
                MetadataConventionIssue(
                    severity=MetadataIssueSeverity.ERROR,
                    location="__data__",
                    message=f"The data cannot be parsed as {data_type}: {message}",
                )
            )
        else:
            if isinstance(metadata, dict):
                parsed_data.attrs = metadata
                checked_obj = parsed_data

    issues = data_issues + [
        issue.model_copy(
            update={
                "location": "__metadata__" + ("" if issue.location == "" else "." + issue.location)
            }
        )
        for issue in check_metadata_conventions(checked_obj, data_type)
    ]
    return MetadataCheckResult(
        valid=all(issue.severity != MetadataIssueSeverity.ERROR for issue in issues),
        issues=issues,
    )
