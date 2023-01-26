from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.exceptions import (
    SinkNotFound,
    SinkNotUnique,
    SourceNotFound,
    SourceNotUnique,
    ThingNodeNotFound,
    ThingNodeNotUnique,
)
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
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


def test_blob_storage_get_thing_nodes_by_parent_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        thing_nodes_with_no_parents = get_thing_nodes_by_parent_id(None)

        assert len(thing_nodes_with_no_parents) == 2
        assert thing_nodes_with_no_parents[0].id == "i"

        thing_nodes_with_parent_i = get_thing_nodes_by_parent_id("i")
        assert len(thing_nodes_with_parent_i) == 3
        assert thing_nodes_with_parent_i[0].id == "i-i"
        assert thing_nodes_with_parent_i[1].id == "i-ii"
        assert thing_nodes_with_parent_i[2].id == "i-iii"

        thing_nodes_with_parent_bla = get_thing_nodes_by_parent_id("bla")
        assert len(thing_nodes_with_parent_bla) == 0


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


def test_blob_storage_get_sources_by_parent_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        sources_with_parent_i_ii = get_sources_by_parent_id("i-ii/E")
        assert len(sources_with_parent_i_ii) == 1
        assert sources_with_parent_i_ii[0].id == "i-ii/E_2022-01-02T14:23:18+00:00"

        sources_with_parent_bla = get_sources_by_parent_id("bla")
        assert len(sources_with_parent_bla) == 0


def test_blob_storage_get_sinks_by_parent_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sinks_with_parent_id_i_iii = get_sinks_by_parent_id("i-iii/F")
        assert len(sinks_with_parent_id_i_iii) == 1
        assert sinks_with_parent_id_i_iii[0].id == "i-iii/F_next"

        sinks_with_parent_bla = get_sinks_by_parent_id("bla")
        assert len(sinks_with_parent_bla) == 0


def test_blob_storage_get_filtered_sources():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        unfiltered_sources = get_filtered_sources(None)
        assert len(unfiltered_sources) == 6

        sources_filtered_by_name = get_filtered_sources("A")
        assert len(sources_filtered_by_name) == 2
        assert sources_filtered_by_name[0].id == "i-i/A_2022-01-02T14:23:18+00:00"
        assert sources_filtered_by_name[1].id == "i-i/A_2022-01-02T14:57:31+00:00"

        sources_filtered_by_date = get_filtered_sources("14")
        assert len(sources_filtered_by_date) == 4
        assert sources_filtered_by_date[0].id == "i-i/A_2022-01-02T14:23:18+00:00"
        assert sources_filtered_by_date[1].id == "i-i/A_2022-01-02T14:57:31+00:00"
        assert sources_filtered_by_date[2].id == "i-i/B_2022-01-02T14:25:56+00:00"
        assert sources_filtered_by_date[3].id == "i-ii/E_2022-01-02T14:23:18+00:00"

        sources_filtered_by_bla = get_filtered_sources("bla")
        assert len(sources_filtered_by_bla) == 0


def test_blob_storage_get_filtered_sinks():
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
        assert sinks_filtered_by_c[0].id == "i-i/C_next"

        sinks_filtered_by_bla = get_filtered_sinks("bla")
        assert len(sinks_filtered_by_bla) == 0


def test_blob_storage_get_thing_node_by_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        thing_node = get_thing_node_by_id("i-ii")
        assert thing_node.id == "i-ii"
        assert thing_node.parentId == "i"
        assert thing_node.name == "ii"
        assert thing_node.description == "Category"

        with pytest.raises(ThingNodeNotFound):
            get_thing_node_by_id("bla")

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
        ):
            with pytest.raises(ThingNodeNotUnique):
                get_thing_node_by_id("i-ii")


def test_blob_storage_get_source_by_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        source_by_id = get_source_by_id("i-i/A_2022-01-02T14:57:31+00:00")
        assert source_by_id.name == "A - 2022-01-02 14:57:31+00:00"
        assert source_by_id.thingNodeId == "i-i/A"

        with pytest.raises(SourceNotFound):
            get_source_by_id("bla")

    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=[
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00",
            ),
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00",
            ),
        ],
    ):
        with pytest.raises(SourceNotUnique):
            get_source_by_id("i-i/A_2022-01-02T14:57:31+00:00")


def test_blob_storage_get_sink_by_id():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sink_by_id = get_sink_by_id("i-i/A_next")
        assert sink_by_id.name == "A - Next Object"
        assert sink_by_id.thingNodeId == "i-i/A"

        with pytest.raises(SinkNotFound):
            get_sink_by_id("bla")

        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.sinks",
            new_callable=mock.PropertyMock,
            return_value=[
                BlobStorageStructureSink(
                    id="i-i/A_next",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
                BlobStorageStructureSink(
                    id="i-i/A_next",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
            ],
        ):
            with pytest.raises(SinkNotUnique):
                get_sink_by_id("i-i/A_next")


def test_blob_storage_get_source_by_thing_node_id_and_metadata_key():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=source_list,
    ):
        source_by_tn_id_and_md_key = get_source_by_thing_node_id_and_metadata_key(
            thing_node_id="i-i/A", metadata_key="A - 2022-01-02 14:57:31+00:00"
        )
        assert source_by_tn_id_and_md_key.id == "i-i/A_2022-01-02T14:57:31+00:00"
        assert source_by_tn_id_and_md_key.thingNodeId == "i-i/A"
        assert source_by_tn_id_and_md_key.name == "A - 2022-01-02 14:57:31+00:00"
        assert source_by_tn_id_and_md_key.path == "i-i/A"
        assert source_by_tn_id_and_md_key.metadataKey == "A - 2022-01-02 14:57:31+00:00"

        with pytest.raises(SourceNotFound):
            get_source_by_thing_node_id_and_metadata_key(
                thing_node_id="i-i/B", metadata_key="A - 2022-01-02 14:57:31+00:00"
            )

    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.create_sources",
        return_value=[
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00",
            ),
            BlobStorageStructureSource(
                id="i-i/A_2022-01-02T14:57:31+00:00",
                thingNodeId="i-i/A",
                name="A - 2022-01-02 14:57:31+00:00",
                path="i-i/A",
                metadataKey="A - 2022-01-02 14:57:31+00:00",
            ),
        ],
    ):
        with pytest.raises(SourceNotUnique):
            source_by_tn_id_and_md_key = get_source_by_thing_node_id_and_metadata_key(
                thing_node_id="i-i/A", metadata_key="A - 2022-01-02 14:57:31+00:00"
            )


def test_blob_storage_get_sink_by_thing_node_id_and_metadata_key():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
        return_value=AdapterHierarchy.from_file(
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
        ),
    ):
        sink_by_tn_id_and_md_key = get_sink_by_thing_node_id_and_metadata_key(
            thing_node_id="i-i/A", metadata_key="A - Next Object"
        )
        assert sink_by_tn_id_and_md_key.id == "i-i/A_next"
        assert sink_by_tn_id_and_md_key.thingNodeId == "i-i/A"
        assert sink_by_tn_id_and_md_key.name == "A - Next Object"
        assert sink_by_tn_id_and_md_key.path == "i-i/A"
        assert sink_by_tn_id_and_md_key.metadataKey == "A - Next Object"

        with pytest.raises(SinkNotFound):
            get_sink_by_thing_node_id_and_metadata_key(
                thing_node_id="i-i/B", metadata_key="A - Next Object"
            )
        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.sinks",
            new_callable=mock.PropertyMock,
            return_value=[
                BlobStorageStructureSink(
                    id="i-i/A_next",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
                BlobStorageStructureSink(
                    id="i-i/A_next",
                    thingNodeId="i-i/A",
                    name="A - Next Object",
                    path="i-i/A",
                    metadataKey="A - Next Object",
                ),
            ],
        ):
            with pytest.raises(SinkNotUnique):
                sink_by_tn_id_and_md_key = get_sink_by_thing_node_id_and_metadata_key(
                    thing_node_id="i-i/A", metadata_key="A - Next Object"
                )
