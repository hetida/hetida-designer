import pytest


@pytest.mark.asyncio
async def test_access_kafka_adapter_info(
    open_async_test_client_for_external_sources_tests,
) -> None:
    response = await open_async_test_client_for_external_sources_tests.get(
        "adapters/external_sources/info"
    )
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_external_sources_adapter_get_structure_from_webservice(
    open_async_test_client_for_external_sources_tests,
):
    response = await open_async_test_client_for_external_sources_tests.get(
        "/adapters/external_sources/structure"
    )

    assert response.status_code == 200

    resp_obj = response.json()

    assert len(resp_obj["thingNodes"]) == 1

    first_thing_node = resp_obj["thingNodes"][0]
    first_thing_node_id = resp_obj["thingNodes"][0]["id"]

    response = await open_async_test_client_for_external_sources_tests.get(
        f"/adapters/external_sources/thingNodes/{first_thing_node_id}"
    )

    assert response.status_code == 200
    assert response.json() == first_thing_node

    response = await open_async_test_client_for_external_sources_tests.get(
        f"/adapters/external_sources/thingNodes/{first_thing_node_id}/metadata"
    )
    assert response.status_code == 200

    assert len(response.json()) == 0
