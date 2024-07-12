from copy import deepcopy
from unittest import mock

import nest_asyncio
import pytest
from httpx import AsyncClient

from hetdesrun.adapters.blob_storage.exceptions import (
    MissingHierarchyError,
    StorageAuthenticationError,
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.models import AdapterHierarchy
from hetdesrun.adapters.exceptions import AdapterConnectionError

nest_asyncio.apply()


@pytest.mark.asyncio
async def test_access_blob_storage_adapter_info(
    async_test_client_with_blob_storage_adapter: AsyncClient,
) -> None:
    async with async_test_client_with_blob_storage_adapter as ac:
        response = await ac.get("adapters/blob/info")
    assert response.status_code == 200
    assert "version" in response.json()


async def walk_thing_nodes(
    parent_id: str,
    tn_append_list: list[dict],
    src_append_list: list[dict],
    snk_append_list: list[dict],
    src_attached_metadata_dict: dict,
    snk_attached_metadata_dict: dict,
    tn_attached_metadata_dict: dict,
    open_async_test_client_with_blob_storage_adapter: AsyncClient,
) -> None:
    print("walk_thing_nodes call with parent_id=" + parent_id)
    """Recursively walk thingnodes"""
    response_obj = (
        await open_async_test_client_with_blob_storage_adapter.get(
            f"/adapters/blob/structure?parentId={parent_id}"
        )
    ).json()

    src_append_list += response_obj["sources"]

    snk_append_list += response_obj["sinks"]

    for src in response_obj["sources"]:
        metadata = (
            await open_async_test_client_with_blob_storage_adapter.get(
                f'/adapters/blob/sources/{src["id"]}/metadata/'
            )
        ).json()
        for metadatum in metadata:
            src_attached_metadata_dict[(src["id"], metadatum["key"])] = metadatum

    for snk in response_obj["sinks"]:
        metadata = (
            await open_async_test_client_with_blob_storage_adapter.get(
                f'/adapters/blob/sinks/{snk["id"]}/metadata/'
            )
        ).json()
        for metadatum in metadata:
            snk_attached_metadata_dict[(snk["id"], metadatum["key"])] = metadatum

    metadata_tn = (
        await open_async_test_client_with_blob_storage_adapter.get(
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
            open_async_test_client_with_blob_storage_adapter,
        )


@pytest.mark.asyncio
async def test_resources_offered_from_blob_storage_webservice(
    async_test_client_with_blob_storage_adapter_with_mocked_structure: AsyncClient,
) -> None:
    async with async_test_client_with_blob_storage_adapter_with_mocked_structure as client:
        response = await client.get("/adapters/blob/structure")
        assert response.status_code == 200

        response_obj = response.json()
        assert len(response_obj["sources"]) == 0
        assert len(response_obj["sinks"]) == 0

        roots = response_obj["thingNodes"]
        assert len(roots) == 2

        all_tns: list[dict] = deepcopy(roots)
        all_srcs: list[dict] = []
        all_snks: list[dict] = []
        tn_attached_metadata_dict: dict = {}
        src_attached_metadata_dict: dict = {}
        snk_attached_metadata_dict: dict = {}

        for root in roots:
            await walk_thing_nodes(
                root["id"],
                tn_append_list=all_tns,
                src_append_list=all_srcs,
                snk_append_list=all_snks,
                src_attached_metadata_dict=src_attached_metadata_dict,
                snk_attached_metadata_dict=snk_attached_metadata_dict,
                tn_attached_metadata_dict=tn_attached_metadata_dict,
                open_async_test_client_with_blob_storage_adapter=client,
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
            response_obj = (await client.get(f'/adapters/blob/sources/{src["id"]}')).json()
            for key in src:
                assert response_obj[key] == src[key]

        for snk in all_snks:
            response_obj = (await client.get(f'/adapters/blob/sinks/{snk["id"]}')).json()
            for key in snk:
                assert response_obj[key] == snk[key]

        for tn in all_tns:
            response_obj = (await client.get(f'/adapters/blob/thingNodes/{tn["id"]}')).json()
            for key in tn:
                assert response_obj[key] == tn[key]


@pytest.mark.asyncio
async def test_blob_adapter_webservice_filtered(
    async_test_client_with_blob_storage_adapter: AsyncClient,
    mocked_blob_storage_sources,
) -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy.from_file(
                "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
            ),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_all_sources",
            return_value=mocked_blob_storage_sources,
        ),
    ):
        async with async_test_client_with_blob_storage_adapter as client:
            sink_response = await client.get("/adapters/blob/sinks", params={"filter": "ii"})
            source_response = await client.get(
                "/adapters/blob/sources", params={"filter": "_2022-01-02T"}
            )

        assert sink_response.status_code == 200
        assert sink_response.json()["resultCount"] == 4
        assert sink_response.json()["sinks"][0]["id"] == "i-ii/E_generic_sink"
        assert sink_response.json()["sinks"][1]["id"] == "i-iii/F_generic_sink"
        assert sink_response.json()["sinks"][2]["id"] == "i-iii/G_generic_sink"
        assert sink_response.json()["sinks"][3]["id"] == "iii/x/C_generic_sink"

        assert source_response.status_code == 200
        assert source_response.json()["resultCount"] == 4
        assert source_response.json()["sources"][:3] == mocked_blob_storage_sources[:3]
        assert source_response.json()["sources"][3] == mocked_blob_storage_sources[5]


@pytest.mark.asyncio
async def test_blob_adapter_webservice_exceptions(  # noqa: PLR0915
    async_test_client_with_blob_storage_adapter_with_mocked_structure: AsyncClient,
) -> None:
    async with async_test_client_with_blob_storage_adapter_with_mocked_structure as client:
        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_thing_nodes_by_parent_id",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_get_structure_response = await client.get("/adapters/blob/structure")

            assert missing_hierarchy_get_structure_response.status_code == 500
            assert (
                "Could not get structure"
                in missing_hierarchy_get_structure_response.json()["detail"]
            )
            assert (
                "hierarchy json is missing"
                in missing_hierarchy_get_structure_response.json()["detail"]
            )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.webservice.get_thing_nodes_by_parent_id",
                return_value=[],
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.webservice.get_sinks_by_parent_id",
                return_value=[],
            ),
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.webservice.get_sources_by_parent_id",
                side_effect=StorageAuthenticationError,
            ):
                invalid_endpoint_get_structure_response = await client.get(
                    "/adapters/blob/structure"
                )

                assert invalid_endpoint_get_structure_response.status_code == 500
                assert (
                    "Could not get structure"
                    in missing_hierarchy_get_structure_response.json()["detail"]
                )
                assert (
                    "endpoint url is invalid"
                    in invalid_endpoint_get_structure_response.json()["detail"]
                )

            with mock.patch(
                "hetdesrun.adapters.blob_storage.webservice.get_sources_by_parent_id",
                side_effect=AdapterConnectionError,
            ):
                invalid_endpoint_get_structure_response = await client.get(
                    "/adapters/blob/structure"
                )

                assert invalid_endpoint_get_structure_response.status_code == 500
                assert (
                    "Could not get structure"
                    in missing_hierarchy_get_structure_response.json()["detail"]
                )
                assert (
                    "problems connecting"
                    in invalid_endpoint_get_structure_response.json()["detail"]
                )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_filtered_sources",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_get_sources_response = await client.get("/adapters/blob/sources")

            assert missing_hierarchy_get_sources_response.status_code == 500
            assert (
                "Could not get sources" in missing_hierarchy_get_sources_response.json()["detail"]
            )
            assert (
                "hierarchy json is missing"
                in missing_hierarchy_get_sources_response.json()["detail"]
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_filtered_sources",
            side_effect=StorageAuthenticationError,
        ):
            invalid_endpoint_get_sources_response = await client.get("/adapters/blob/sources")

            assert invalid_endpoint_get_sources_response.status_code == 500
            assert "Could not get sources" in invalid_endpoint_get_sources_response.json()["detail"]
            assert (
                "endpoint url is invalid" in invalid_endpoint_get_sources_response.json()["detail"]
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_filtered_sources",
            side_effect=AdapterConnectionError,
        ):
            connection_error_get_sources_response = await client.get("/adapters/blob/sources")

            assert connection_error_get_sources_response.status_code == 500
            assert "Could not get sources" in connection_error_get_sources_response.json()["detail"]
            assert "problems connecting" in connection_error_get_sources_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_filtered_sinks",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_get_sinks_response = await client.get("/adapters/blob/sinks")

            assert missing_hierarchy_get_sinks_response.status_code == 500
            assert "Could not get sinks" in missing_hierarchy_get_sinks_response.json()["detail"]
            assert (
                "hierarchy json is missing" in missing_hierarchy_get_sinks_response.json()["detail"]
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_source_by_id",
            side_effect=StructureObjectNotFound,
        ):
            no_source_response = await client.get(
                "/adapters/blob/sources/i-i/A_2022-01-02T14:23:18+00:00"
            )

            assert no_source_response.status_code == 404
            assert "Could not find source" in no_source_response.json()["detail"]
            assert (
                "with id 'i-i/A_2022-01-02T14:23:18+00:00'" in no_source_response.json()["detail"]
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_source_by_id",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_sources_response = await client.get(
                "/adapters/blob/sources/i-i/A_2022-01-02T14:23:18+00:00"
            )

            assert missing_hierarchy_sources_response.status_code == 500
            assert (
                "with id 'i-i/A_2022-01-02T14:23:18+00:00'"
                in missing_hierarchy_sources_response.json()["detail"]
            )
            assert (
                "hierarchy json is missing" in missing_hierarchy_sources_response.json()["detail"]
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_source_by_id",
            side_effect=StorageAuthenticationError,
        ):
            invalid_endpoint_sources_response = await client.get(
                "/adapters/blob/sources/i-i/A_2022-01-02T14:23:18+00:00"
            )

            assert invalid_endpoint_sources_response.status_code == 500
            assert (
                "with id 'i-i/A_2022-01-02T14:23:18+00:00'"
                in invalid_endpoint_sources_response.json()["detail"]
            )
            assert "endpoint url is invalid" in invalid_endpoint_sources_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_source_by_id",
            side_effect=AdapterConnectionError,
        ):
            connection_error_sources_response = await client.get(
                "/adapters/blob/sources/i-i/A_2022-01-02T14:23:18+00:00"
            )

            assert connection_error_sources_response.status_code == 500
            assert (
                "with id 'i-i/A_2022-01-02T14:23:18+00:00'"
                in connection_error_sources_response.json()["detail"]
            )
            assert "problems connecting" in connection_error_sources_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_sink_by_id",
            side_effect=StructureObjectNotFound,
        ):
            no_sink_response = await client.get("/adapters/blob/sinks/i-i/A_generic_sink")

            assert no_sink_response.status_code == 404
            assert "Could not find sink" in no_sink_response.json()["detail"]
            assert "with id 'i-i/A_generic_sink'" in no_sink_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_sink_by_id",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_sinks_response = await client.get(
                "/adapters/blob/sinks/i-i/A_generic_sink"
            )

            assert missing_hierarchy_sinks_response.status_code == 500
            assert (
                "with id 'i-i/A_generic_sink'" in missing_hierarchy_sinks_response.json()["detail"]
            )
            assert "hierarchy json is missing" in missing_hierarchy_sinks_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_thing_node_by_id",
            side_effect=StructureObjectNotFound,
        ):
            no_thing_node_response = await client.get("/adapters/blob/thingNodes/i-i/A")

            assert no_thing_node_response.status_code == 404
            assert "Could not find thing node" in no_thing_node_response.json()["detail"]
            assert "with id 'i-i/A'" in no_thing_node_response.json()["detail"]

        with mock.patch(
            "hetdesrun.adapters.blob_storage.webservice.get_thing_node_by_id",
            side_effect=MissingHierarchyError,
        ):
            missing_hierarchy_thing_nodes_response = await client.get(
                "/adapters/blob/thingNodes/i-i/A_generic_sink"
            )

            assert missing_hierarchy_thing_nodes_response.status_code == 500
            assert (
                "with id 'i-i/A_generic_sink'"
                in missing_hierarchy_thing_nodes_response.json()["detail"]
            )
            assert (
                "hierarchy json is missing"
                in missing_hierarchy_thing_nodes_response.json()["detail"]
            )
