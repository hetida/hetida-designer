import nest_asyncio
import pytest

nest_asyncio.apply()


@pytest.mark.asyncio
async def test_access_blob_storage_adapter_info(async_test_client):
    async with async_test_client as ac:
        response = await ac.get("adapters/blob/info")
    assert response.status_code == 200
    assert "version" in response.json().keys()


async def walk_thing_nodes(
    parent_id,
    tn_append_list,
    src_append_list,
    snk_append_list,
    src_attached_metadata_dict,
    snk_attached_metadata_dict,
    tn_attached_metadata_dict,
    open_async_test_client,
):
    """Recursively walk thingnodes"""
    response_obj = (
        await open_async_test_client.get(
            f"/adapters/blob/structure?parentId={parent_id}"
        )
    ).json()
    src_append_list += response_obj["sources"]
    snk_append_list += response_obj["sinks"]

    for src in response_obj["sources"]:
        metadata = (
            await open_async_test_client.get(
                f'/adapters/blob/sources/{src["id"]}/metadata/'
            )
        ).json()
        for metadatum in metadata:
            src_attached_metadata_dict[(src["id"], metadatum["key"])] = metadatum

    for snk in response_obj["sinks"]:
        metadata = (
            await open_async_test_client.get(
                f'/adapters/blob/sinks/{snk["id"]}/metadata/'
            )
        ).json()
        for metadatum in metadata:
            snk_attached_metadata_dict[(snk["id"], metadatum["key"])] = metadatum

    metadata_tn = (
        await open_async_test_client.get(
            f"/adapters/blob/thingNodes/{parent_id}/metadata/"
        )
    ).json()
    for metadatum in metadata_tn:
        tn_attached_metadata_dict[(parent_id, metadatum["key"])] = metadatum

    for tn in response_obj["thingNodes"]:
        tn_append_list.append(tn)
        await walk_thing_nodes(
            tn["id"],
            tn_append_list,
            src_append_list,
            snk_append_list,
            src_attached_metadata_dict,
            snk_attached_metadata_dict,
            tn_attached_metadata_dict,
            open_async_test_client,
        )


@pytest.mark.asyncio
async def test_resources_offered_from_blob_storage_webservice(
    async_test_client,
):
    """Walks through the hierarchy provided by structure endpoint and gets/posts offered resources"""
    async with async_test_client as client:

        response_obj = (await client.get("/adapters/blob/structure")).json()

        assert len(response_obj["sources"]) == 0
        assert len(response_obj["sinks"]) == 0

        roots = response_obj["thingNodes"]
        assert len(roots) == 1

        root = roots[0]

        all_tns = roots
        all_srcs = []
        all_snks = []
        tn_attached_metadata_dict = {}
        src_attached_metadata_dict = {}
        snk_attached_metadata_dict = {}

        await walk_thing_nodes(
            root["id"],
            tn_append_list=all_tns,
            src_append_list=all_srcs,
            snk_append_list=all_snks,
            src_attached_metadata_dict=src_attached_metadata_dict,
            snk_attached_metadata_dict=snk_attached_metadata_dict,
            tn_attached_metadata_dict=tn_attached_metadata_dict,
            open_async_test_client=client,
        )

        assert len(all_tns) == 11
        assert len(all_srcs) == 6
        assert len(all_snks) == 7

        assert len(src_attached_metadata_dict) == 0
        assert len(snk_attached_metadata_dict) == 0
        assert len(tn_attached_metadata_dict) == 0

        for src in all_srcs:
            response_obj = (
                await client.get(f'/adapters/blob/sources/{src["id"]}')
            ).json()
            for key in src.keys():
                assert response_obj[key] == src[key]

        for snk in all_snks:
            response_obj = (
                await client.get(f'/adapters/blob/sinks/{snk["id"]}')
            ).json()
            for key in snk.keys():
                assert response_obj[key] == snk[key]

        for tn in all_tns:
            response_obj = (
                await client.get(f'/adapters/blob/thingNodes/{tn["id"]}')
            ).json()
            for key in tn.keys():
                assert response_obj[key] == tn[key]
