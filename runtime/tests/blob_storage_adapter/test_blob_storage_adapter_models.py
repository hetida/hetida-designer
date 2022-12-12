import logging
from datetime import datetime, timezone
from typing import List
from unittest import mock

import pytest
from pydantic import ValidationError

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    ThingNodeInvalidError,
)
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    BucketName,
    Category,
    IdString,
    ObjectKey,
    StructureThingNode,
    ThingNodeName,
    find_duplicates,
)


@pytest.mark.skip("ConstrainedStr does seem to not behave as expected")
def test_blob_storage_class_thing_node_name():
    ThingNodeName("I")

    with pytest.raises(ValidationError):
        # shorter than min_length
        ThingNodeName("")

    with pytest.raises(ValidationError):
        # violates regex
        ThingNodeName("ä")

    with pytest.raises(ValidationError):
        # longer than max_length
        ThingNodeName(
            "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII"
        )


@pytest.mark.skip("ConstrainedStr does seem to not behave as expected")
def test_blob_storage_class_bucket_name():
    BucketName("i")

    with pytest.raises(ValidationError):
        # shorter than min_length
        BucketName("")

    with pytest.raises(ValidationError):
        # violates regex
        BucketName("I")

    with pytest.raises(ValidationError):
        # longer than max_length
        BucketName("IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII")


@pytest.mark.skip("ConstrainedStr does seem to not behave as expected")
def test_blob_storage_class_id_string():
    IdString("i-ii/A_0123")

    with pytest.raises(ValidationError):
        # shorter than min_length
        IdString("")

    with pytest.raises(ValidationError):
        # violates regex
        IdString("~")


def test_blob_storage_class_object_key():
    with pytest.raises(ValidationError):
        object_key = ObjectKey(
            string="A_2022Y01M02D14h23m18s",
            name="A",
            time=datetime(
                year=2022,
                month=1,
                day=2,
                hour=14,
                minute=23,
                second=18,
            ),
        )

    object_key = ObjectKey(
        string="A_2022Y01M02D14h23m18s",
        name="A",
        time=datetime(
            year=2022,
            month=1,
            day=2,
            hour=14,
            minute=23,
            second=18,
            tzinfo=timezone.utc,
        ),
    )

    assert object_key.string == "A_2022Y01M02D14h23m18s"
    assert object_key.name == "A"
    assert object_key.time == datetime(
        year=2022, month=1, day=2, hour=14, minute=23, second=18, tzinfo=timezone.utc
    )

    object_key_from_name = ObjectKey.from_name("B")
    object_key_from_string = ObjectKey.from_string(object_key_from_name.string)
    assert object_key_from_name == object_key_from_string

    thing_node_id = object_key.to_thing_node_id(bucket_name="i-ii")
    assert thing_node_id == "i-ii/A"

    with pytest.raises(ValueError):
        ObjectKey.from_string("A")


def test_blob_storage_class_structure_source():
    source = BlobStorageStructureSource(
        id="i-ii/A_2022Y01M02D14h23m18s",
        thingNodeId="i-ii/A",
        name="A - 2022-01-02 14:23:18+00:00",
        path="i-ii/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00",
    )

    assert source.id == "i-ii/A_2022Y01M02D14h23m18s"
    assert source.thingNodeId == "i-ii/A"
    assert source.name == "A - 2022-01-02 14:23:18+00:00"
    assert source.path == "i-ii/A"
    assert source.metadataKey == "A - 2022-01-02 14:23:18+00:00"
    assert source.type == "metadata(any)"
    assert source.visible == True
    assert source.filters == {}

    src_bucket_name, src_object_key = source.to_bucket_name_and_object_key()
    src_from_bkt_and_ok = BlobStorageStructureSource.from_bucket_name_and_object_key(
        bucket_name=src_bucket_name, object_key=src_object_key
    )
    assert src_from_bkt_and_ok == source

    with pytest.raises(ValidationError):
        # invalid id due to no object key dir separator
        BlobStorageStructureSource(
            id="A_2022Y01M02D14h23m18s",
            thingNodeId="A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # invalid id due to bucket name part invalid
        BlobStorageStructureSource(
            id="I-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # invalid id due to object key part invalid
        BlobStorageStructureSource(
            id="i-ii/A2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # thingNodeId does not match id
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/B",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # name does not match id due to thing node name
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="B - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # name does not match id due to timestamp
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2023-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # path does not match thingNodeId
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/B",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # metadataKey does not match name
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="B - 2022-01-02 14:23:18+00:00",
        )


def test_blob_storage_class_structure_sink():
    sink = BlobStorageStructureSink(
        id="i-ii/A_next",
        thingNodeId="i-ii/A",
        name="A - Next Object",
        path="i-ii/A",
        metadataKey="A - Next Object",
    )

    assert sink.id == "i-ii/A_next"
    assert sink.thingNodeId == "i-ii/A"
    assert sink.name == "A - Next Object"
    assert sink.path == "i-ii/A"
    assert sink.metadataKey == "A - Next Object"
    assert sink.type == "metadata(any)"
    assert sink.visible == True
    assert sink.filters == {}

    snk_bucket_name, snk_object_key = sink.to_bucket_name_and_object_key()
    assert snk_bucket_name == "i-ii"
    assert snk_object_key.name == "A"

    sink_from_thing_node = BlobStorageStructureSink.from_thing_node(
        thing_node=StructureThingNode(
            id="i-ii/A",
            parentId="i-ii",
            name="A",
            description="",
        )
    )

    assert sink_from_thing_node == sink

    with pytest.raises(ValidationError):
        # thingNodeId does not match id
        BlobStorageStructureSource(
            id="i-ii/A_next",
            thingNodeId="i-ii/B",
            name="A - Next Trained Model",
            path="i-ii/A",
            metadataKey="A - Next Trained Model",
        )

    with pytest.raises(ValidationError):
        # name does not match id
        BlobStorageStructureSource(
            id="i-ii/A_next",
            thingNodeId="i-ii/A",
            name="B - Next Trained Model",
            path="i-ii/A",
            metadataKey="A - Next Trained Model",
        )

    with pytest.raises(ValidationError):
        # path does not match thingNodeId
        BlobStorageStructureSink(
            id="i-ii/A_next",
            thingNodeId="i-ii/A",
            name="A - Next Trained Model",
            path="i-ii/A",
            metadataKey="B - Next Trained Model",
        )

    with pytest.raises(ValidationError):
        # metadataKey does not match name
        BlobStorageStructureSink(
            id="i-ii/A_next",
            thingNodeId="i-ii/A",
            name="A - Next Trained Model",
            path="i-ii/A",
            metadataKey="B - Next Trained Model",
        )


def test_blob_storage_class_category():
    category = Category(
        name="I",
        description="Category",
        substructure=[
            Category(name="A", description="Subcategory"),
            Category(name="B", description="Subcategory"),
        ],
    )

    assert category.name == "I"
    assert category.description == "Category"
    assert len(category.substructure) == 2
    assert isinstance(category.substructure[0], Category)
    assert category.substructure[0].name == "A"
    assert category.substructure[0].description == "Subcategory"
    assert category.substructure[0].substructure == None
    assert category.substructure[0].level == None
    assert category.substructure[1].name == "B"
    assert category.substructure[1].description == "Subcategory"
    assert category.substructure[1].substructure == None
    assert category.substructure[1].level == None
    assert category.level is None

    depth = category.set_level_and_get_depth(level=2)
    assert depth == 3
    assert category.level == 2
    assert category.substructure[0].level == 3
    assert category.substructure[1].level == 3

    thing_node_from_category = category.to_thing_node(parent_id="i", separator="-")
    assert thing_node_from_category.id == "i-i"
    assert thing_node_from_category.parentId == "i"
    assert thing_node_from_category.name == "I"
    assert thing_node_from_category.description == "Category"

    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []
    category.create_structure(
        thing_nodes=thing_nodes,
        bucket_names=bucket_names,
        sinks=sinks,
        bucket_level=2,
        parent_id="i",
    )
    assert len(thing_nodes) == 3
    assert thing_nodes[0].id == "i-i"
    assert thing_nodes[0].parentId == "i"
    assert thing_nodes[0].name == "I"
    assert thing_nodes[1].id == "i-i/A"
    assert thing_nodes[1].parentId == "i-i"
    assert thing_nodes[1].name == "A"
    assert thing_nodes[2].id == "i-i/B"
    assert thing_nodes[2].parentId == "i-i"
    assert thing_nodes[2].name == "B"
    assert len(bucket_names) == 1
    assert bucket_names[0] == BucketName("i-i")
    assert len(sinks) == 2
    assert sinks[0].id == "i-i/A_next"
    assert sinks[0].thingNodeId == "i-i/A"
    assert sinks[0].name == "A - Next Object"
    assert sinks[1].id == "i-i/B_next"
    assert sinks[1].thingNodeId == "i-i/B"
    assert sinks[1].name == "B - Next Object"


def test_blob_storage_utils_find_duplicates():
    item_list = ["apple", "banana", "cherry", "apple", "banana"]
    duplicates = find_duplicates(item_list)

    assert len(duplicates) == 2
    assert "apple" in duplicates
    assert "banana" in duplicates


def test_blob_storage_class_adapter_hierarchy():
    adapter_hierarchy = AdapterHierarchy(
        **{
            "bucket_level": 2,
            "structure": [
                {
                    "name": "I",
                    "description": "Super Category",
                    "substructure": [
                        {
                            "name": "i",
                            "description": "Category",
                            "substructure": [
                                {
                                    "name": "A",
                                    "description": "Subcategory",
                                    "substructure": [],
                                },
                                {
                                    "name": "B",
                                    "description": "Subcategory",
                                    "substructure": None,
                                },
                                {"name": "C", "description": "Subcategory"},
                                {"name": "D", "description": "Subcategory"},
                            ],
                        },
                        {
                            "name": "ii",
                            "description": "Category",
                            "substructure": [
                                {"name": "E", "description": "Subcategory"}
                            ],
                        },
                        {
                            "name": "iii",
                            "description": "Category",
                            "substructure": [
                                {"name": "F", "description": "Subcategory"},
                                {"name": "G", "description": "Subcategory"},
                            ],
                        },
                    ],
                }
            ],
        }
    )

    assert adapter_hierarchy.bucket_level == 2
    assert adapter_hierarchy.structure[0].level == 1
    assert adapter_hierarchy.structure[0].substructure[0].level == 2
    assert adapter_hierarchy.structure[0].substructure[0].substructure[0].level == 3

    thing_nodes = adapter_hierarchy.thing_nodes
    bucket_names = adapter_hierarchy.bucket_names
    sinks = adapter_hierarchy.sinks

    assert len(thing_nodes) == 11
    assert len(bucket_names) == 3
    assert len(sinks) == 7


@pytest.mark.skip("Error message not in log")
def test_blob_storage_class_adapter_hierarchy_with_thing_node_invalid_error(caplog):
    bucket_level = 2
    structure = [
        Category(
            **{
                "name": "I",
                "description": "Super Category",
                "substructure": [
                    {
                        "name": "i",
                        "description": "Category",
                        "substructure": [
                            {"name": "C", "description": "Subcategory"},
                        ],
                    },
                ],
            }
        )
    ]
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.Category.to_thing_node",
            side_effect=ThingNodeInvalidError,
        ):
            AdapterHierarchy(bucket_level=bucket_level, structure=structure)

        assert "ValidationError for transformation of category " in caplog.text


@pytest.mark.skip("ConstrainedStr does seem to not behave as expected")
def test_blob_storage_class_adapter_hierarchy_with_name_invalid_error(caplog):
    bucket_level = 2
    structure = [
        Category(
            **{
                "name": "IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
                "description": "Super Category",
                "substructure": [
                    {
                        "name": "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",
                        "description": "Category",
                        "substructure": [
                            {"name": "C", "description": "Subcategory"},
                        ],
                    },
                ],
            }
        )
    ]
    with caplog.at_level(logging.INFO):
        caplog.clear()
        with pytest.raises(BucketNameInvalidError):

            AdapterHierarchy(bucket_level=bucket_level, structure=structure)
        assert (
            "ValidationError for transformation of "
            "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii-iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii to BucketName"
        ) in caplog.text
