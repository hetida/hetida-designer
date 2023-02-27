from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.exceptions import (
    StructureObjectNotFound,
    StructureObjectNotUnique,
)
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    IdString,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.structure import (
    get_filtered_sinks,
    get_filtered_sources,
    get_sink_by_id,
    get_sink_by_thing_node_id_and_metadata_key,
    get_sinks_by_parent_id,
    get_source_by_id,
    get_source_by_thing_node_id_and_metadata_key,
    get_sources_by_parent_id,
    get_thing_node_by_id,
    get_thing_nodes_by_parent_id,
)


def test_blob_storage_get_thing_nodes_by_parent_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        thing_nodes_with_no_parents = get_thing_nodes_by_parent_id(None)

        assert len(thing_nodes_with_no_parents) == 2
        assert thing_nodes_with_no_parents[0].id == "i"

        thing_nodes_with_parent_i = get_thing_nodes_by_parent_id(IdString("i"))
        assert len(thing_nodes_with_parent_i) == 3
        assert thing_nodes_with_parent_i[0].id == "i-i"
        assert thing_nodes_with_parent_i[1].id == "i-ii"
        assert thing_nodes_with_parent_i[2].id == "i-iii"

        thing_nodes_with_parent_bla = get_thing_nodes_by_parent_id(IdString("bla"))
        assert len(thing_nodes_with_parent_bla) == 0


source_list = [
    BlobStorageStructureSource(
        id="i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
    ),
    BlobStorageStructureSource(
        id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
    ),
    BlobStorageStructureSource(
        id="i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51",
        thingNodeId="i-i/B",
        name="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51",
        path="i-i/B",
        metadataKey="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-03-08T17:23:18+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa",
        thingNodeId="i-i/D",
        name="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa",
        path="i-i/D",
        metadataKey="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-04-02T13:28:29+00:00_af77087b-a064-4ff9-9c4a-d23b2c503ade",
        thingNodeId="i-i/D",
        name="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade",
        path="i-i/D",
        metadataKey="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade",
    ),
    BlobStorageStructureSource(
        id="i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144",
        thingNodeId="i-ii/E",
        name="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144",
        path="i-ii/E",
        metadataKey="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144",
    ),
]


@pytest.mark.asyncio
async def test_blob_storage_get_sources_by_parent_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        sources_with_parent_i_ii = await get_sources_by_parent_id(IdString("i-ii/E"))
        assert len(sources_with_parent_i_ii) == 1
        assert (
            sources_with_parent_i_ii[0].id
            == "i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144"
        )

        sources_with_parent_bla = await get_sources_by_parent_id(IdString("bla"))
        assert len(sources_with_parent_bla) == 0


def test_blob_storage_get_sinks_by_parent_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sinks_with_parent_id_i_iii = get_sinks_by_parent_id(IdString("i-iii/F"))
        assert len(sinks_with_parent_id_i_iii) == 1
        assert sinks_with_parent_id_i_iii[0].id == "i-iii/F_generic_sink"

        sinks_with_parent_bla = get_sinks_by_parent_id(IdString("bla"))
        assert len(sinks_with_parent_bla) == 0


@pytest.mark.asyncio
async def test_blob_storage_get_filtered_sources() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        unfiltered_sources = await get_filtered_sources(None)
        assert len(unfiltered_sources) == 6

        sources_filtered_by_name = await get_filtered_sources("A")
        assert len(sources_filtered_by_name) == 2
        assert (
            sources_filtered_by_name[0].id
            == "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )
        assert (
            sources_filtered_by_name[1].id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )

        sources_filtered_by_date = await get_filtered_sources("14")
        assert len(sources_filtered_by_date) == 4
        assert (
            sources_filtered_by_date[0].id
            == "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )
        assert (
            sources_filtered_by_date[1].id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert (
            sources_filtered_by_date[2].id
            == "i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
        )
        assert (
            sources_filtered_by_date[3].id
            == "i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144"
        )

        sources_filtered_by_bla = await get_filtered_sources("bla")
        assert len(sources_filtered_by_bla) == 0


def test_blob_storage_get_filtered_sinks() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        unfiltered_sinks = get_filtered_sinks(None)
        assert len(unfiltered_sinks) == 8

        sinks_filtered_by_c = get_filtered_sinks("C")
        assert len(sinks_filtered_by_c) == 2
        assert sinks_filtered_by_c[0].id == "i-i/C_generic_sink"

        sinks_filtered_by_bla = get_filtered_sinks("bla")
        assert len(sinks_filtered_by_bla) == 0


def test_blob_storage_get_thing_node_by_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        thing_node = get_thing_node_by_id(IdString("i-ii"))
        assert thing_node.id == "i-ii"
        assert thing_node.parentId == "i"
        assert thing_node.name == "ii"
        assert thing_node.description == "Category"

        with pytest.raises(StructureObjectNotFound):
            get_thing_node_by_id(IdString("bla"))

        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.thing_nodes",
            new_callable=mock.PropertyMock,
            return_value=[
                StructureThingNode(
                    id="i-ii", parentId="i", name="ii", description="Category"
                ),
                StructureThingNode(
                    id="i-ii", parentId="i", name="ii", description="Kategory"
                ),
            ],
        ), pytest.raises(StructureObjectNotUnique):
            get_thing_node_by_id(IdString("i-ii"))


@pytest.mark.asyncio
async def test_blob_storage_get_source_by_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        source_by_id = await get_source_by_id(
            IdString(
                "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
            )
        )
        assert (
            source_by_id.name
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert source_by_id.thingNodeId == "i-i/A"

        with pytest.raises(StructureObjectNotFound):
            await get_source_by_id(IdString("bla"))

    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=[
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
            ),
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
            ),
        ],
    ), pytest.raises(StructureObjectNotUnique):
        await get_source_by_id(
            IdString(
                "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
            )
        )


def test_blob_storage_get_sink_by_id() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sink_by_id = get_sink_by_id(IdString("i-i/A_generic_sink"))
        assert sink_by_id.name == "A - Next Object"
        assert sink_by_id.thingNodeId == "i-i/A"

        with pytest.raises(StructureObjectNotFound):
            get_sink_by_id(IdString("bla"))

        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.sinks",
            new_callable=mock.PropertyMock,
            return_value=[
                BlobStorageStructureSink(
                    id="i-i/A_generic_sink",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
                BlobStorageStructureSink(
                    id="i-i/A_generic_sink",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
            ],
        ), pytest.raises(StructureObjectNotUnique):
            get_sink_by_id(IdString("i-i/A_generic_sink"))


@pytest.mark.asyncio
async def test_blob_storage_get_source_by_thing_node_id_and_metadata_key() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        source_by_tn_id_and_md_key = await get_source_by_thing_node_id_and_metadata_key(
            thing_node_id=IdString("i-i/A"),
            metadata_key="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
        )
        assert (
            source_by_tn_id_and_md_key.id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert source_by_tn_id_and_md_key.thingNodeId == "i-i/A"
        assert (
            source_by_tn_id_and_md_key.name
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert source_by_tn_id_and_md_key.path == "i-i/A"
        assert (
            source_by_tn_id_and_md_key.metadataKey
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )

        with pytest.raises(StructureObjectNotFound):
            await get_source_by_thing_node_id_and_metadata_key(
                thing_node_id=IdString("i-i/B"),
                metadata_key="A - 2022-01-02 14:57:31+00:00",
            )

    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=[
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
            ),
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
            ),
        ],
    ), pytest.raises(StructureObjectNotUnique):
        source_by_tn_id_and_md_key = await get_source_by_thing_node_id_and_metadata_key(
            thing_node_id=IdString("i-i/A"),
            metadata_key="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43",
        )


def test_blob_storage_get_sink_by_thing_node_id_and_metadata_key() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sink_by_tn_id_and_md_key = get_sink_by_thing_node_id_and_metadata_key(
            thing_node_id=IdString("i-i/A"), metadata_key="A - Next Object"
        )
        assert sink_by_tn_id_and_md_key.id == "i-i/A_generic_sink"
        assert sink_by_tn_id_and_md_key.thingNodeId == "i-i/A"
        assert sink_by_tn_id_and_md_key.name == "A - Next Object"
        assert sink_by_tn_id_and_md_key.path == "i-i/A"
        assert sink_by_tn_id_and_md_key.metadataKey == "A - Next Object"

        with pytest.raises(StructureObjectNotFound):
            get_sink_by_thing_node_id_and_metadata_key(
                thing_node_id=IdString("i-i/B"), metadata_key="A - Next Object"
            )

        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.sinks",
            new_callable=mock.PropertyMock,
            return_value=[
                BlobStorageStructureSink(
                    id="i-i/A_generic_sink",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
                BlobStorageStructureSink(
                    id="i-i/A_generic_sink",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
            ],
        ), pytest.raises(StructureObjectNotUnique):
            sink_by_tn_id_and_md_key = get_sink_by_thing_node_id_and_metadata_key(
                thing_node_id=IdString("i-i/A"), metadata_key="A - Next Object"
            )
