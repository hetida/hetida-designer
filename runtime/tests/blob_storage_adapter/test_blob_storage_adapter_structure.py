from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.exceptions import (
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSource,
    HierarchyNode,
    IdString,
    StructureBucket,
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
        id="i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
    ),
    BlobStorageStructureSource(
        id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl",
        thingNodeId="i-i/A",
        name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)",
        path="i-i/A",
        metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)",
    ),
    BlobStorageStructureSource(
        id="i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl",
        thingNodeId="i-i/B",
        name="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51 (pkl)",
        path="i-i/B",
        metadataKey="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51 (pkl)",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-03-08T17:23:18+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa.pkl",
        thingNodeId="i-i/D",
        name="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",
        path="i-i/D",
        metadataKey="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",
    ),
    BlobStorageStructureSource(
        id="i-i/D_2022-04-02T13:28:29+00:00_af77087b-a064-4ff9-9c4a-d23b2c503ade.pkl",
        thingNodeId="i-i/D",
        name="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade (pkl)",
        path="i-i/D",
        metadataKey="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade (pkl)",
    ),
    BlobStorageStructureSource(
        id="i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144.pkl",
        thingNodeId="i-ii/E",
        name="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144 (pkl)",
        path="i-ii/E",
        metadataKey="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144 (pkl)",
    ),
]

source_by_thing_node_id_dict: dict[IdString, list[BlobStorageStructureSource]] = {}
for src in source_list:
    if src.thingNodeId not in source_by_thing_node_id_dict:
        source_by_thing_node_id_dict[src.thingNodeId] = [src]
    else:
        source_by_thing_node_id_dict[src.thingNodeId].append(src)


async def mocked_get_oks_in_bucket(bucket_name: StructureBucket) -> list[IdString]:
    if bucket_name == "i-i":
        return [
            IdString("A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"),
            IdString("A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl"),
            IdString("A_test"),
        ]
    if bucket_name == "i-ii":
        return [
            IdString("B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl"),
            IdString("D_2022-03-08T17:23:18+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa.pkl"),
            IdString("D_2022-04-02T13:28:29+00:00_af77087b-a064-4ff9-9c4a-d23b2c503ade.pkl"),
        ]
    raise ValueError("bucket_name must be 'i-i' or 'i-ii'!")


@pytest.mark.asyncio
async def test_blob_storage_get_sources_by_parent_id() -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy(
                structure=(
                    HierarchyNode(
                        name="I",
                        description="",
                        substructure=(
                            HierarchyNode(
                                name="I",
                                description="",
                                substructure=[
                                    HierarchyNode(name="A", description=""),
                                    HierarchyNode(name="B", description=""),
                                ],
                            ),
                        ),
                    ),
                ),
            ),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_object_key_strings_in_bucket",
            new=mocked_get_oks_in_bucket,
        ),
    ):
        parent_id = IdString("i-i/A")
        sources_from_parent_id = await get_sources_by_parent_id(parent_id)

        assert len(sources_from_parent_id) == 2

        too_high_parent_id = IdString("i-i")
        sources_from_too_high_parent_id = await get_sources_by_parent_id(too_high_parent_id)

        assert len(sources_from_too_high_parent_id) == 0

        structure_not_matching_parent_id = IdString("i-ii/A")
        with pytest.raises(StructureObjectNotFound, match=r"parent id.* does not occur"):
            await get_sources_by_parent_id(structure_not_matching_parent_id)


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
        "hetdesrun.adapters.blob_storage.structure.get_all_sources",
        return_value=source_list,
    ):
        unfiltered_sources = await get_filtered_sources(None)
        assert len(unfiltered_sources) == 6

        sources_filtered_by_name = await get_filtered_sources("A")
        assert len(sources_filtered_by_name) == 2
        assert (
            sources_filtered_by_name[0].id
            == "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
        )
        assert (
            sources_filtered_by_name[1].id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl"
        )

        sources_filtered_by_date = await get_filtered_sources("14")
        assert len(sources_filtered_by_date) == 4
        assert (
            sources_filtered_by_date[0].id
            == "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
        )
        assert (
            sources_filtered_by_date[1].id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl"
        )
        assert (
            sources_filtered_by_date[2].id
            == "i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl"
        )
        assert (
            sources_filtered_by_date[3].id
            == "i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144.pkl"
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


@pytest.mark.asyncio
async def test_blob_storage_get_source_by_id() -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy(
                structure=(
                    HierarchyNode(
                        name="I",
                        description="",
                        substructure=(
                            HierarchyNode(
                                name="I",
                                description="",
                                substructure=[
                                    HierarchyNode(name="A", description=""),
                                    HierarchyNode(name="B", description=""),
                                ],
                            ),
                        ),
                    ),
                ),
            ),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_object_key_strings_in_bucket",
            new=mocked_get_oks_in_bucket,
        ),
    ):
        source_id = IdString(
            "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
        )

        source = await get_source_by_id(source_id)

        assert (
            source.name
            == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
        )

        structure_not_matching_source_id = IdString(
            "i-ii/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl"
        )
        with pytest.raises(StructureObjectNotFound, match="No thing node matching"):
            await get_source_by_id(structure_not_matching_source_id)

        source_id_without_object_key = IdString(
            "i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl"
        )
        with pytest.raises(StructureObjectNotFound, match="no object"):
            await get_source_by_id(source_id_without_object_key)


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


def mocked_get_thing_node_by_id(thing_node_id: IdString) -> StructureThingNode:
    thing_node_dict = {
        IdString("i-i/A"): StructureThingNode(
            id=IdString("i-i/A"), parentId=IdString("i-i"), name="A", description=""
        )
    }
    if thing_node_id not in thing_node_dict:
        raise StructureObjectNotFound(f"Found no thing node with id {thing_node_id}!")
    return thing_node_dict[thing_node_id]


@pytest.mark.asyncio
async def test_blob_storage_get_source_by_thing_node_id_and_metadata_key() -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_thing_node_by_id",
            new=mocked_get_thing_node_by_id,
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy.from_file(
                "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
            ),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_object_key_strings_in_bucket",
            return_value=[
                "A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl",
                "A_2022-01-02T14:57:31+02:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl",
            ],
        ),
    ):
        source_by_tn_id_and_md_key = await get_source_by_thing_node_id_and_metadata_key(
            thing_node_id=IdString("i-i/A"),
            metadata_key=(
                "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)"
            ),
        )
        assert (
            source_by_tn_id_and_md_key.id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl"
        )
        assert source_by_tn_id_and_md_key.thingNodeId == "i-i/A"
        assert (
            source_by_tn_id_and_md_key.name
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)"
        )
        assert source_by_tn_id_and_md_key.path == "i-i/A"
        assert (
            source_by_tn_id_and_md_key.metadataKey
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)"
        )

        with pytest.raises(
            StructureObjectNotFound,
            match="Thing node id.*and metadata key.* do not match",
        ):
            await get_source_by_thing_node_id_and_metadata_key(
                thing_node_id=IdString("i-i/B"),
                metadata_key=(
                    "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)"
                ),
            )

        with pytest.raises(StructureObjectNotFound, match="must have timezone UTC"):
            await get_source_by_thing_node_id_and_metadata_key(
                thing_node_id=IdString("i-i/A"),
                metadata_key=(
                    "A - 2022-01-02 14:57:31+02:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)"
                ),
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
