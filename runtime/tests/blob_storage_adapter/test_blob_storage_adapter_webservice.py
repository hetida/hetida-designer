from copy import deepcopy
from unittest import mock

import nest_asyncio
import pytest

from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSource,
)

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
    print("walk_thing_nodes call with parent_id=" + parent_id)
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
        print("add thingNode with id=" + tn["id"] + " and call walk_thing_nodes")
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


source_list = [
    BlobStorageStructureSource(
        id="i-i/A_2022-01-02T14:23:18+00:00",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:23:18+00:00",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00",
    ),
    BlobStorageStructureSource(
        id="i-i/A_2022-01-02T14:57:31+00:00",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:57:31+00:00",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:57:31+00:00",
    ),
    BlobStorageStructureSource(
        id="i-i/B_2022-01-02T14:25:56+00:00",
        thingNodeId="i-i/B",
        name="B - 2022-01-02 14:25:56+00:00",
        path="i-i/B",
        metadataKey="B - 2022-01-02 14:25:56+00:00",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-03-08T17:23:18+00:00",
        thingNodeId="i-i/D",
        name="D - 2022-03-08 17:23:18+00:00",
        path="i-i/D",
        metadataKey="D - 2022-03-08 17:23:18+00:00",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-04-02T13:28:29+00:00",
        thingNodeId="i-i/D",
        name="D - 2022-04-02 13:28:29+00:00",
        path="i-i/D",
        metadataKey="D - 2022-04-02 13:28:29+00:00",
    ),
    BlobStorageStructureSource(
        id="i-ii/E_2022-01-02T14:23:18+00:00",
        thingNodeId="i-ii/E",
        name="E - 2022-01-02 14:23:18+00:00",
        path="i-ii/E",
        metadataKey="E - 2022-01-02 14:23:18+00:00",
    ),
]


@pytest.mark.asyncio
async def test_resources_offered_from_blob_storage_webservice(
    async_test_client,
):
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.structure.create_sources",
            return_value=source_list,
        ):
            """Walks through the hierarchy provided by structure endpoint and gets/posts offered resources"""
            async with async_test_client as client:

                response_obj = (await client.get("/adapters/blob/structure")).json()

                assert len(response_obj["sources"]) == 0
                assert len(response_obj["sinks"]) == 0

                roots = response_obj["thingNodes"]
                assert len(roots) == 2

                all_tns = deepcopy(roots)
                all_srcs = []
                all_snks = []
                tn_attached_metadata_dict = {}
                src_attached_metadata_dict = {}
                snk_attached_metadata_dict = {}

                for root in roots:
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
                print("all_tns")
                for tn in all_tns:
                    print(tn["id"])
                assert len(all_tns) == 14
                assert len(all_srcs) == 6
                assert len(all_snks) == 8

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
