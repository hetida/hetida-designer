from typing import Any

import pytest
from fastapi import FastAPI
from hdhelpers.metadata.conventions import (
    MULTITSFRAME_METADATA_EXAMPLE,
    SERIES_METADATA_EXAMPLE,
)
from httpx import AsyncClient

SIGNAL_ID = "7ab8c419-8745-4714-b588-57c0c772cc95"


def value_dimension(column: str = "value", **fields: Any) -> dict[str, Any]:
    return {"column": column, "unit": None, "measurement": None} | fields


def metric(metric_id: str, **fields: Any) -> dict[str, Any]:
    return {
        "id": metric_id,
        "name": f"name of {metric_id}",
        "value_dimensions": [value_dimension()],
    } | fields


def dataset_metadata(**fields: Any) -> dict[str, Any]:
    return {
        "metric_key": "id",
        "queried_metrics": [],
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
    } | fields


def series_metadata(**metric_fields: Any) -> dict[str, Any]:
    return {
        "dataset_metadata": dataset_metadata(single_metric="a", queried_metrics=["a"]),
        "metrics": [metric("a", **metric_fields)],
    }


# a comment as the hetida platform sends it: Jackson serializes Instants as UTC isoformat strings
# with Z and includes null fields
platform_comment: dict[str, Any] = {
    "id": "0b5f0f0e-6d1c-4f7e-9a51-1f3c2a9e8d11",
    "start_date": "2026-10-18T06:00:00Z",
    "end_date": "2026-10-18T07:30:00Z",
    "created_at": "2026-10-18T08:12:45.123Z",
    "edited_at": None,
    "content": "Pump maintenance",
    "username": "jdoe",
    "tags": ["maintenance"],
    "replies": [
        {
            "id": "5e1c7d2a-8b3f-4c6e-9d0a-2f4b6c8e0a13",
            "created_at": "2026-10-18T09:00:00Z",
            "edited_at": "2026-10-18T09:05:00.500Z",
            "content": "Done, pump runs again",
            "username": "asmith",
        }
    ],
}

# the metadata the hetida platform sends for a timeseries of a SERIES read
platform_series_metadata: dict[str, Any] = {
    "dataset_metadata": {
        "metric_key": "id",
        "single_metric": SIGNAL_ID,
        "queried_metrics": [SIGNAL_ID],
        "signal_group": None,
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
        "ref_data_frequency": None,
        "ref_data_frequency_offset": None,
        "invalidation_interval_start": None,
        "invalidation_interval_end": None,
        "invalidation_interval_type": None,
        "invalidate_dataset": None,
        "delete_invalidated": None,
        "only_invalidate": None,
        "ref_dataset_discrete": None,
        "invalidation_timestamp": None,
        "new_data_invalidation_date": None,
    },
    "metrics": [
        {
            "id": SIGNAL_ID,
            "external_id": "water.north.level",
            "name": "Water-lvl-north",
            "display_name": None,
            "description": None,
            # property values of the platform, possibly as strings
            "inherited": {"signal_role": "level", "latitude": "51.43"},
            "comments": [
                platform_comment,
                # a comment on a single point in time without tags and replies
                platform_comment
                | {
                    "start_date": "2026-10-18T12:00:00Z",
                    "end_date": "2026-10-18T12:00:00Z",
                    "tags": [],
                    "replies": [],
                },
            ],
            "value_dimensions": [
                {
                    "column": "value",
                    "name": "Water-lvl-north",
                    "display_name": None,
                    "short_display_name": None,
                    "description": None,
                    "unit": "m",
                    "measurement": "level",
                    "value_data_type": "float",
                }
            ],
            "default_aggregation_method": "AVG",
        }
    ],
}

# the metadata the hetida platform sends for a MULTITSFRAME read of a signal group
platform_multitsframe_metadata: dict[str, Any] = {
    "dataset_metadata": platform_series_metadata["dataset_metadata"]
    | {
        "single_metric": None,
        "queried_metrics": [SIGNAL_ID, "pump"],
        "signal_group": {"id": "3c2e1d4f", "name": "Pumps north", "description": None},
    },
    "metrics": [
        platform_series_metadata["metrics"][0] | {"display_name": "Water level"},
        platform_series_metadata["metrics"][0]
        | {
            "id": "pump",
            "external_id": None,
            "comments": [],
            "value_dimensions": [value_dimension()],
            "default_aggregation_method": None,
        },
    ],
}


@pytest.mark.filterwarnings(
    "ignore:Duplicate Operation ID receive_execution_response__callback_url__post "
    "for function receive_execution_response:UserWarning"
)
def test_metadata_conventions_in_openapi(app_without_auth: FastAPI) -> None:
    openapi = app_without_auth.openapi()
    component_schemas = openapi["components"]["schemas"]

    assert {
        "SeriesMetadata",
        "SingleTSFrameMetadata",
        "MultiTSFrameMetadata",
        "SingleMetricDatasetMetadata",
        "MultiTSFrameDatasetMetadata",
        "MetricMetadata",
        "ValueDimensionMetadata",
        "SharedValueDimensionMetadata",
        "InheritedMetricMetadata",
        "MetricComment",
        "AggregationMethod",
        "IntervalType",
        "RecordingMode",
    } <= set(component_schemas)
    assert component_schemas["SeriesMetadata"]["examples"] == [SERIES_METADATA_EXAMPLE]
    assert component_schemas["MultiTSFrameMetadata"]["examples"] == [MULTITSFRAME_METADATA_EXAMPLE]
    assert set(component_schemas["MetricMetadata"]["required"]) == {
        "id",
        "name",
        "value_dimensions",
    }
    assert set(component_schemas["ValueDimensionMetadata"]["required"]) == {
        "column",
        "unit",
        "measurement",
    }
    assert "else" in component_schemas["SingleMetricDatasetMetadata"]
    assert component_schemas["MetricMetadata"]["properties"]["channel_id"]["deprecated"] is True
    assert [
        schema["$ref"]
        for schema in component_schemas["WrappedTimeseriesData"]["properties"]["__metadata__"][
            "anyOf"
        ]
    ] == [
        "#/components/schemas/SeriesMetadata",
        "#/components/schemas/SingleTSFrameMetadata",
        "#/components/schemas/MultiTSFrameMetadata",
    ]
    assert "/api/metadata-conventions/check/{data_type}" in openapi["paths"]


CHECK_URL = "/api/metadata-conventions/check/"

multitsframe_data = {
    "timestamp": ["2026-10-18T00:00:00Z", "2026-10-18T00:00:00Z", "2026-10-18T01:00:00Z"],
    "metric": [SIGNAL_ID, "pump", "other"],
    "value": [2.5, 120.0, 80.0],
}


@pytest.mark.asyncio
async def test_check_endpoint(async_test_client: AsyncClient, mocked_clean_test_db_session) -> None:
    async with async_test_client as ac:
        conforming = await ac.post(
            CHECK_URL + "MULTITSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": platform_multitsframe_metadata,
                "__data__": {key: values[:2] for key, values in multitsframe_data.items()},
            },
        )
        inconsistent = await ac.post(
            CHECK_URL + "MULTITSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": platform_multitsframe_metadata,
                "__data__": multitsframe_data,
            },
        )
        with_warning = await ac.post(
            CHECK_URL + "SERIES",
            json={
                "__hd_wrapped_data_object__": "SERIES",
                "__metadata__": series_metadata(units="m"),
                "__data__": {
                    "index": ["2026-10-18T00:00:00Z", "2026-10-18T00:00:00Z"],
                    "data": [1.0, 2.0],
                },
                "__data_parsing_options__": {"orient": "split"},
            },
        )
        unparsable_data = await ac.post(
            CHECK_URL + "SINGLETSFRAME",
            json={
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": [],
                "__data__": {"value": [1.0, 2.0]},
            },
        )
        only_metadata = await ac.post(
            CHECK_URL + "SERIES",
            json={
                "__hd_wrapped_data_object__": "SERIES",
                "__metadata__": series_metadata(value_dimensions=[value_dimension("temp")]),
            },
        )

    assert conforming.status_code == 200
    assert conforming.json() == {"valid": True, "issues": []}

    assert inconsistent.status_code == 200
    assert inconsistent.json()["valid"] is False
    assert [issue["location"] for issue in inconsistent.json()["issues"]] == [
        "__metadata__.metrics",
        "__metadata__.dataset_metadata.queried_metrics",
    ]

    assert with_warning.status_code == 200
    assert with_warning.json()["valid"] is True
    assert [(issue["severity"], issue["location"]) for issue in with_warning.json()["issues"]] == [
        ("warning", "__metadata__.metrics[0].units")
    ]

    assert unparsable_data.status_code == 200
    assert unparsable_data.json()["valid"] is False
    assert [
        (issue["severity"], issue["location"]) for issue in unparsable_data.json()["issues"]
    ] == [
        ("error", "__data__"),
        ("error", "__metadata__"),
    ]
    assert "timestamp" in unparsable_data.json()["issues"][0]["message"]

    assert only_metadata.status_code == 200
    assert only_metadata.json()["valid"] is False
    assert [(issue["severity"], issue["location"]) for issue in only_metadata.json()["issues"]] == [
        ("error", "__metadata__.metrics[0].value_dimensions"),
        ("warning", "__metadata__.metrics[0].value_dimensions[0].column"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data_type", "wrapped_data"),
    [
        ("SERIES", {"__hd_wrapped_data_object__": "DATAFRAME", "__metadata__": {}}),
        ("MULTITSFRAME", {"__hd_wrapped_data_object__": "SERIES", "__metadata__": {}}),
        ("DATAFRAME", {"__hd_wrapped_data_object__": "DATAFRAME", "__metadata__": {}}),
        ("SERIES", {"__hd_wrapped_data_object__": "SERIES", "__metadata": {}}),
        # misspelled optional field, which would be ignored silently otherwise
        ("SERIES", {"__hd_wrapped_data_object__": "SERIES", "__metadata__": {}, "__data": [1.0]}),
        ("SERIES", {"__metadata__": {}, "__data__": [1.0]}),
    ],
)
async def test_check_endpoint_rejects_requests_not_in_wrapped_format(
    async_test_client: AsyncClient,
    mocked_clean_test_db_session,
    data_type: str,
    wrapped_data: dict[str, Any],
) -> None:
    async with async_test_client as ac:
        response = await ac.post(CHECK_URL + data_type, json=wrapped_data)

    assert response.status_code == 422
