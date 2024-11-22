import pytest


@pytest.mark.asyncio
async def test_access_kafka_adapter_info(
    open_async_test_client_with_kafka_adapter,
) -> None:
    response = await open_async_test_client_with_kafka_adapter.get("adapters/kafka/info")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_kafka_adapter_get_structure_from_webservice(
    open_async_test_client_with_kafka_adapter,
):
    response = await open_async_test_client_with_kafka_adapter.get("/adapters/kafka/structure")

    assert response.status_code == 200

    resp_obj = response.json()

    assert len(resp_obj["thingNodes"]) == 1

    first_thing_node = resp_obj["thingNodes"][0]
    first_thing_node_id = resp_obj["thingNodes"][0]["id"]

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/thingNodes/{first_thing_node_id}"
    )

    assert response.status_code == 200
    assert response.json() == first_thing_node

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/thingNodes/{first_thing_node_id}/metadata"
    )
    assert response.status_code == 200

    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_kafka_adapter_sources(
    open_async_test_client_with_kafka_adapter,
):
    response = await open_async_test_client_with_kafka_adapter.get("/adapters/kafka/sources")

    assert response.status_code == 200

    resp_obj = response.json()
    assert len(resp_obj["sources"]) == 21

    first_source = resp_obj["sources"][0]
    first_source_id = first_source["id"]

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/sources/{first_source_id}"
    )
    assert response.status_code == 200
    assert response.json() == first_source

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/sources/{first_source_id}/metadata/"
    )

    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_kafka_adapter_sinks(
    open_async_test_client_with_kafka_adapter,
):
    response = await open_async_test_client_with_kafka_adapter.get("/adapters/kafka/sinks")

    assert response.status_code == 200

    resp_obj = response.json()

    assert len(resp_obj["sinks"]) == 21

    first_sink = resp_obj["sinks"][0]
    first_sink_id = first_sink["id"]

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/sinks/{first_sink_id}"
    )
    assert response.status_code == 200
    assert response.json() == first_sink

    response = await open_async_test_client_with_kafka_adapter.get(
        f"/adapters/kafka/sinks/{first_sink_id}/metadata/"
    )

    assert response.status_code == 200
    assert len(response.json()) == 0
