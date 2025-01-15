import uuid

import pytest


@pytest.mark.asyncio
async def test_access_vst_adapter_info(
    async_test_client_with_vst_adapter,
):
    response = await async_test_client_with_vst_adapter.get("adapters/virtual_structure/info")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_vst_adapter_get_structure_with_none_from_webservice(
    async_test_client_with_vst_adapter,
):
    """Tests whether the root node is returned when no parent_id is provided."""

    response = await async_test_client_with_vst_adapter.get("/adapters/virtual_structure/structure")

    assert response.status_code == 200

    resp_obj = response.json()

    # Verify that only the root node is returned
    assert len(resp_obj["thingNodes"]) == 1
    assert resp_obj["thingNodes"][0]["parentId"] is None

    first_thing_node = resp_obj["thingNodes"][0]
    first_thing_node_id = resp_obj["thingNodes"][0]["id"]

    response = await async_test_client_with_vst_adapter.get(
        f"/adapters/virtual_structure/thingNodes/{first_thing_node_id}"
    )

    # Verify that the thingNodes endpoint returns the same node
    # given its ID
    assert response.status_code == 200
    assert response.json() == first_thing_node


@pytest.mark.asyncio
async def test_vst_adapter_get_structure_from_webservice(async_test_client_with_vst_adapter):
    """Tests the normal behavior of the structure endpoint."""

    # Track current node ID to iterate through the structure hierarchy
    current_node_id = None

    for expected_thing_nodes_count, expected_sinks_count, expected_sources_count in [
        (1, 0, 0),  # First level: root thingnode
        (2, 0, 0),  # Second level: two thingnodes
        (1, 0, 0),  # Third level: one thingnode
        (0, 1, 3),  # Final level: one sink and three sources
    ]:
        # Fetch the structure using the current node ID as the parentId
        response = await async_test_client_with_vst_adapter.get(
            "/adapters/virtual_structure/structure",
            params={"parentId": current_node_id} if current_node_id else {},
        )
        assert response.status_code == 200

        resp_obj = response.json()

        # Verify the expected number of thingnodes, sinks, and sources at this level
        assert len(resp_obj["thingNodes"]) == expected_thing_nodes_count
        assert len(resp_obj["sinks"]) == expected_sinks_count
        assert len(resp_obj["sources"]) == expected_sources_count

        # If there are child thingnodes, proceed down the hierarchy by updating `current_node_id`
        if resp_obj["thingNodes"]:
            current_node_id = resp_obj["thingNodes"][0]["id"]


@pytest.mark.asyncio
async def test_vst_adapter_metadata_endpoints(async_test_client_with_vst_adapter):
    random_uuid = uuid.uuid4()  # Non-existent UUID
    endpoints = [
        f"/adapters/virtual_structure/thingNodes/{random_uuid}/metadata/",
        f"/adapters/virtual_structure/sources/{random_uuid}/metadata/",
        f"/adapters/virtual_structure/sinks/{random_uuid}/metadata/",
    ]
    for endpoint in endpoints:
        response = await async_test_client_with_vst_adapter.get(endpoint)
        # All metadata endpoints are hardcoded to return empty lists
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint", "entity_type"),
    [
        ("/adapters/virtual_structure/thingNodes", "ThingNode"),
        ("/adapters/virtual_structure/sources", "Source"),
        ("/adapters/virtual_structure/sinks", "Sink"),
    ],
)
async def test_vst_adapter_endpoints_with_non_existent_id(
    async_test_client_with_vst_adapter, endpoint, entity_type
):
    random_uuid = uuid.uuid4()  # Non-existent UUID
    response = await async_test_client_with_vst_adapter.get(f"{endpoint}/{random_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == f"No {entity_type} found for provided UUID: {random_uuid}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint", "filter_value", "expected_name"),
    [
        ("/adapters/virtual_structure/sources", "PrEsEt", "Energy usage with preset filter"),
        (
            "/adapters/virtual_structure/sinks",
            "AnOmAly",  # Use this capitalization to test case-insensitivity
            "Anomaly score for the energy usage of the pump system in Storage Tank",
        ),
    ],
)
async def test_sources_and_sinks_endpoints_with_filter_strings(
    async_test_client_with_vst_adapter, endpoint, filter_value, expected_name
):
    """Tests whether sources and sinks are correctly retrieved in search."""
    response = await async_test_client_with_vst_adapter.get(
        endpoint, params={"filter": filter_value}
    )
    assert response.status_code == 200
    resp_obj = response.json()
    assert len(resp_obj["sources" if "sources" in endpoint else "sinks"]) == 1
    assert resp_obj["sources" if "sources" in endpoint else "sinks"][0]["name"] == expected_name
