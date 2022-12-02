import nest_asyncio
import pytest

nest_asyncio.apply()


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
async def test_access_blob_storage_adapter_info(async_test_client):
    async with async_test_client as ac:
        response = await ac.get("adapters/blob/info")
    assert response.status_code == 200
    assert "version" in response.json().keys()
