import pytest


@pytest.mark.asyncio
async def test_access_component_adapter_info(
    open_async_test_client_for_component_adapter_tests,
) -> None:
    response = await open_async_test_client_for_component_adapter_tests.get(
        "adapters/component/info"
    )
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
@pytest.mark.usefixtures("_components_for_component_adapter_tests")
async def test_component_adapter_get_structure_from_webservice(
    mocked_clean_test_db_session,
    open_async_test_client_for_component_adapter_tests,
):
    response = await open_async_test_client_for_component_adapter_tests.get(
        "/adapters/component/structure"
    )

    assert response.status_code == 200

    resp_obj = response.json()

    assert len(resp_obj["thingNodes"]) == 4
    assert len(resp_obj["sources"]) == 0
    assert len(resp_obj["sinks"]) == 0

    total_number_sources_from_structure = 0

    for tn in resp_obj["thingNodes"]:
        tn_struct_response = await open_async_test_client_for_component_adapter_tests.get(
            f"/adapters/component/structure?parentId={tn['id']}"
        )

        assert tn_struct_response.status_code == 200
        tn_struct_resp_obj = tn_struct_response.json()

        # no thing nodes on second level:
        assert len(tn_struct_resp_obj["thingNodes"]) == 0

        for src in tn_struct_resp_obj["sources"]:
            src_resp = await open_async_test_client_for_component_adapter_tests.get(
                f"/adapters/component/sources/{src['id']}"
            )
            assert src_resp.status_code == 200
            assert src_resp.json() == src
            total_number_sources_from_structure += 1

        assert len(tn_struct_resp_obj["sinks"]) == 0

    assert total_number_sources_from_structure == 1
    # TODO: more tests for structure endpoint
    # TODO: test other endpoints


@pytest.mark.asyncio
@pytest.mark.usefixtures("_components_for_component_adapter_tests")
async def test_component_adapter_get_ssources_from_webservice(
    mocked_clean_test_db_session,
    open_async_test_client_for_component_adapter_tests,
):
    response = await open_async_test_client_for_component_adapter_tests.get(
        "/adapters/component/sources"
    )

    assert response.status_code == 200

    resp_obj = response.json()

    assert len(resp_obj["sources"]) == 1

    # all sources should occur via the single source endpoint!
    for src in resp_obj["sources"]:
        src_resp = await open_async_test_client_for_component_adapter_tests.get(
            "/adapters/component/sources/" + src["id"]
        )
        assert src_resp.status_code == 200
        assert src_resp.json() == src
