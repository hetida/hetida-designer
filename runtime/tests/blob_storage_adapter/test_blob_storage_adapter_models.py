from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from hetdesrun.adapters.blob_storage.models import (
    BlobStorageAdapterConfig,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    BucketName,
    Category,
    IdString,
    ObjectKey,
    StructureThingNode,
    ThingNodeName,
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
        # invalid id
        BlobStorageStructureSource(
            id="A_2022Y01M02D14h23m18s",
            thingNodeId="A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="A",
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
        # name does not match id
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="B - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00",
        )

    with pytest.raises(ValidationError):
        # path does not match thingNodeId
        BlobStorageStructureSource(
            id="i-ii/A_2022Y01M02D14h23m18s",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00",
            path="i-ii/A",
            metadataKey="B - 2022-01-02 14:23:18+00:00",
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
        name="A - Next Trained Model",
        path="i-ii/A",
        metadataKey="A - Next Trained Model",
    )

    assert sink.id == "i-ii/A_next"
    assert sink.thingNodeId == "i-ii/A"
    assert sink.name == "A - Next Trained Model"
    assert sink.path == "i-ii/A"
    assert sink.metadataKey == "A - Next Trained Model"
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


def test_blob_storage_class_adapter_config():
    config = BlobStorageAdapterConfig(
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

    assert config.bucket_level == 2
    assert config.structure[0].level == 1
    assert config.structure[0].substructure[0].level == 2
    assert config.structure[0].substructure[0].substructure[0].level == 3
