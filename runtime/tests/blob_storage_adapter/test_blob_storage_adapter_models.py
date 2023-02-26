from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from hetdesrun.adapters.blob_storage import (
    BUCKET_NAME_DIR_SEPARATOR,
    GENERIC_SINK_ID_SUFFIX,
    GENERIC_SINK_NAME_SUFFIX,
    HIERARCHY_END_NODE_NAME_SEPARATOR,
    IDENTIFIER_SEPARATOR,
    OBJECT_KEY_DIR_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.exceptions import MissingHierarchyError
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    HierarchyNode,
    IdString,
    ObjectKey,
    StructureBucket,
    StructureThingNode,
    find_duplicates,
)


def test_blob_storage_class_structure_bucket() -> None:
    StructureBucket(name="iii")

    with pytest.raises(ValidationError):
        # shorter than min_length
        StructureBucket(name="ii")

    with pytest.raises(ValidationError):
        # violates regex
        StructureBucket(name="III")

    with pytest.raises(ValidationError):
        # longer than max_length
        StructureBucket(
            name="iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii"
        )


def test_blob_storage_class_object_key() -> None:
    with pytest.raises(ValueError, match="UTC") as exc_info:
        object_key = ObjectKey(
            string="A_2022-01-02T14:23:18+00:00",
            name="A",
            time=datetime(
                year=2022,
                month=1,
                day=2,
                hour=14,
                minute=23,
                second=18,
                tzinfo=timezone(timedelta(hours=1)),
            ),
            job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
        )
    assert "The ObjectKey attribute time must have timezone UTC!" in str(exc_info.value)

    object_key = ObjectKey(
        string="A_2022-01-02T14:23:18+00:00",
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
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
    )

    assert object_key.string == "A_2022-01-02T14:23:18+00:00"
    assert object_key.name == "A"
    assert object_key.time == datetime(
        year=2022, month=1, day=2, hour=14, minute=23, second=18, tzinfo=timezone.utc
    )

    object_key_from_name = ObjectKey.from_name_and_job_id(
        IdString("B"), job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f")
    )
    object_key_from_string = ObjectKey.from_string(object_key_from_name.string)
    assert object_key_from_name == object_key_from_string

    thing_node_id = object_key.to_thing_node_id(bucket=StructureBucket(name="i-ii"))
    assert thing_node_id == "i-ii/A"

    with pytest.raises(
        ValueError, match=f"contains '{IDENTIFIER_SEPARATOR}' less than"
    ) as exc_info:
        ObjectKey.from_string(
            IdString("A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f")
        )
    assert (
        f"not a valid ObjectKey string, because it contains '{IDENTIFIER_SEPARATOR}'"
        in str(exc_info.value)
    )


def test_blob_storage_class_structure_thing_node() -> None:
    StructureThingNode(id="i-ii", parentId="i", name="II", description="")
    thing_node = StructureThingNode(id="i-ii/A", parentId="i-ii", name="A", description="")

    structure_bucket, object_key =thing_node.to_bucket_name_and_object_key(metadata_key="A - 2001-02-03T04:05:06+00:00 - e54d527d-70c7-4ac7-8b67-7aa8ec7b5ebe")
    assert structure_bucket.name == "i-ii"
    assert object_key.string == "A_2001-02-03T04:05:06+00:00_e54d527d-70c7-4ac7-8b67-7aa8ec7b5ebe"

    with pytest.raises(ValidationError) as exc_info:
        # ThingNodeName shorter than min_length
        StructureThingNode(id="i-ii/A", name="", description="")
    assert "ensure this value has at least 1 characters" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # IdString shorter than min_length
        StructureThingNode(id="", name="A", description="")
    assert "ensure this value has at least 1 characters" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # ThingNodeName violates regex
        StructureThingNode(id="i-ii/A", name="ä", description="")
    assert 'string does not match regex "^[a-zA-Z0-9]+$"' in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # IdString violates regex
        StructureThingNode(id="~", name="A", description="")
    assert 'string does not match regex "^[a-zA-Z0-9:+\\-/_-]+$"' in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # ThingNodeName longer than max_length
        StructureThingNode(
            id="i-ii/A",
            name="IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
            description="",
        )
    assert "ensure this value has at most 63 characters" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # id does not consist of parentId and name combined with bucket name or object key separator
        StructureThingNode(id="i-ii/A", parentId="i-i", name="A", description="")

    assert "The id 'i-ii/A' of a thing node must consist of " in str(exc_info.value)
    assert "its parent id 'i-i' connected by" in str(exc_info.value)
    assert f"one of the separators '{BUCKET_NAME_DIR_SEPARATOR}'" in str(exc_info.value)
    assert f"or '{OBJECT_KEY_DIR_SEPARATOR}' with its name 'A'!" in str(exc_info.value)


def test_blob_storage_class_structure_source_works() -> None:
    source = BlobStorageStructureSource(
        id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        thingNodeId="i-ii/A",
        name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        path="i-ii/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
    )

    assert (
        source.id
        == "i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert source.thingNodeId == "i-ii/A"
    assert (
        source.name
        == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert source.path == "i-ii/A"
    assert (
        source.metadataKey
        == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert source.type == "metadata(any)"
    assert source.visible is True
    assert source.filters == {}

    src_bucket_name, src_object_key = source.to_structure_bucket_and_object_key()
    src_from_bkt_and_ok = (
        BlobStorageStructureSource.from_structure_bucket_and_object_key(
            bucket=src_bucket_name, object_key=src_object_key
        )
    )
    assert src_from_bkt_and_ok == source

    multi_level_ok_src_from_bkt_and_ok = (
        BlobStorageStructureSource.from_structure_bucket_and_object_key(
            bucket=StructureBucket(name="iii"),
            object_key=ObjectKey.from_string(
                IdString(
                    "x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
                )
            ),
        )
    )
    assert (
        multi_level_ok_src_from_bkt_and_ok.id
        == "iii/x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert (
        multi_level_ok_src_from_bkt_and_ok.name
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert multi_level_ok_src_from_bkt_and_ok.thingNodeId == "iii/x/C"
    assert (
        multi_level_ok_src_from_bkt_and_ok.metadataKey
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
    )
    assert multi_level_ok_src_from_bkt_and_ok.path == "iii/x/C"


def test_blob_storage_class_structure_source_raises_exceptions() -> None:
    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to no object key dir separator
        BlobStorageStructureSource(
            id="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert f"must contain at least one '{OBJECT_KEY_DIR_SEPARATOR}'" in str(
        exc_info.value
    )

    # TODO: make classes inheriting from ConstrainedStr raise errors!
    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to bucket name part invalid
        BlobStorageStructureSource(
            id="I-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert "The first part 'I-ii'" in str(exc_info.value)
    assert "of the source id 'I-ii/A_2022-01-02T14:23:18+00:00" in str(exc_info.value)
    assert f"before the first '{OBJECT_KEY_DIR_SEPARATOR}'" in str(exc_info.value)
    assert "must correspond to a bucket name!" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to object key part invalid
        BlobStorageStructureSource(
            id="i-ii/A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert (
        "The second part 'A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )
    assert (
        "of the source id 'i-ii/A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )
    assert f"after the first '{OBJECT_KEY_DIR_SEPARATOR}'" in str(exc_info.value)
    assert "must correspond to an object key string!" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # thingNodeId does not match id
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/B",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert "The source's thing node id 'i-ii/B'" in str(exc_info.value)
    assert (
        "does not match its id "
        "'i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # name invalid due to missing separator
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert (
        "The source name 'A 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f' "
        f"must contain the string '{HIERARCHY_END_NODE_NAME_SEPARATOR}' exactly twice!"
        in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # name does not match id due to thing node name
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert (
        "The source name 'B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )
    assert "must start with the name 'A' of the corresponding thing node" in str(
        exc_info.value
    )

    with pytest.raises(ValidationError) as exc_info:
        # name does not match id due to timestamp
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A - 2023-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert (
        "The time of the source's name "
        "'A - 2023-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )
    assert (
        "must match to the time in its id "
        "'i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # path does not match thingNodeId
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/B",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert "The source path" in str(exc_info.value)
    assert "i-ii/B" in str(exc_info.value)
    assert "must be the same string as its thingNodeId" in str(exc_info.value)
    assert "i-ii/A" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # metadataKey does not match name
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            path="i-ii/A",
            metadataKey="B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        )

    assert (
        "The source's metadataKey "
        "'B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )
    assert (
        "must be the same string as its name "
        "'A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f'"
        in str(exc_info.value)
    )


def test_blob_storage_class_structure_sink() -> None:
    sink = BlobStorageStructureSink(
        id="i-ii/A_generic_sink",
        thingNodeId="i-ii/A",
        name="A - Next Object",
        path="i-ii/A",
        metadataKey="A - Next Object",
    )

    assert sink.id == "i-ii/A_generic_sink"
    assert sink.thingNodeId == "i-ii/A"
    assert sink.name == "A - Next Object"
    assert sink.path == "i-ii/A"
    assert sink.metadataKey == "A - Next Object"
    assert sink.type == "metadata(any)"
    assert sink.visible is True
    assert sink.filters == {}

    snk_bucket, snk_object_key = sink.to_structure_bucket_and_object_key(
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f")
    )
    assert snk_bucket.name == "i-ii"
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

    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to no object key dir separator
        BlobStorageStructureSink(
            id="A_generic_sink",
            thingNodeId="A",
            name="A - Next Object",
            path="A",
            metadataKey="A - Next Object",
        )

    assert f"must contain at least one '{OBJECT_KEY_DIR_SEPARATOR}'" in str(
        exc_info.value
    )

    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to bucket name part invalid
        BlobStorageStructureSink(
            id="I-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert "The first part 'I-ii'" in str(exc_info.value)
    assert "of the sink id 'I-ii/A_generic_sink'" in str(exc_info.value)
    assert f"before the first '{OBJECT_KEY_DIR_SEPARATOR}'" in str(exc_info.value)
    assert "must correspond to a bucket name!" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # invalid id due to object key part invalid
        BlobStorageStructureSink(
            id="i-ii/Anext",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert (
        f"The sink id 'i-ii/Anext' must end with '{IDENTIFIER_SEPARATOR}{GENERIC_SINK_ID_SUFFIX}'!"
        in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # thingNodeId does not match id
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/B",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert "The sink's thing node id 'i-ii/B'" in str(exc_info.value)
    assert "does not match its id 'i-ii/A_generic_sink'" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # name invalid due to missing separator
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert (
        "The sink name 'A Next Object' must contain "
        f"the string '{HIERARCHY_END_NODE_NAME_SEPARATOR}'!" in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # name does not match id due to thing node name
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="B - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert "The sink name 'B - Next Object'" in str(exc_info.value)
    assert "must start with the name 'A' of the corresponding thing node" in str(
        exc_info.value
    )

    with pytest.raises(ValidationError) as exc_info:
        # name does not match id due to timestamp
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Trained Model",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    assert (
        f"The sink name 'A - Next Trained Model' must end with '{GENERIC_SINK_NAME_SUFFIX}'"
        in str(exc_info.value)
    )

    with pytest.raises(ValidationError) as exc_info:
        # path does not match thingNodeId
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/B",
            metadataKey="A - Next Object",
        )

    assert "The sink's path 'i-ii/B' must be the same string as" in str(exc_info.value)
    assert "its thingNodeId 'i-ii/A'!" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        # metadataKey does not match name
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="B - Next Object",
        )

    assert "The sink's metadataKey 'B - Next Object' must be" in str(exc_info.value)
    assert "the same string as its name 'A - Next Object'!" in str(exc_info.value)


def test_blob_storage_class_hierarchy_node() -> None:
    hierarchy_node = HierarchyNode(
        name="I",
        description="Category",
        below_structure_defines_object_key=True,
        substructure=[
            HierarchyNode(name="A", description="Subcategory"),
            HierarchyNode(name="B", description="Subcategory"),
        ],
    )

    assert hierarchy_node.name == "I"
    assert hierarchy_node.description == "Category"
    assert hierarchy_node.substructure is not None
    assert len(hierarchy_node.substructure) == 2
    assert isinstance(hierarchy_node.substructure[0], HierarchyNode)
    assert hierarchy_node.substructure[0].name == "A"
    assert hierarchy_node.substructure[0].description == "Subcategory"
    assert hierarchy_node.substructure[0].substructure is None
    assert hierarchy_node.substructure[0].get_depth() == 1
    assert hierarchy_node.substructure[1].name == "B"
    assert hierarchy_node.substructure[1].description == "Subcategory"
    assert hierarchy_node.substructure[1].substructure is None
    assert hierarchy_node.substructure[1].get_depth() == 1
    assert hierarchy_node.get_depth() == 2

    thing_node_from_hierarchy_node = hierarchy_node.to_thing_node(
        parent_id=IdString("i"), separator="-"
    )
    assert thing_node_from_hierarchy_node.id == "i-i"
    assert thing_node_from_hierarchy_node.parentId == "i"
    assert thing_node_from_hierarchy_node.name == "I"
    assert thing_node_from_hierarchy_node.description == "Category"

    thing_nodes: list[StructureThingNode] = []
    bucket_names: list[StructureBucket] = []
    sinks: list[BlobStorageStructureSink] = []
    hierarchy_node.create_structure(
        thing_nodes=thing_nodes,
        buckets=bucket_names,
        sinks=sinks,
        parent_id=IdString("i"),
        part_of_bucket_name=True,
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
    assert bucket_names[0] == StructureBucket(name="i-i")
    assert len(sinks) == 2
    assert sinks[0].id == "i-i/A_generic_sink"
    assert sinks[0].thingNodeId == "i-i/A"
    assert sinks[0].name == "A - Next Object"
    assert sinks[1].id == "i-i/B_generic_sink"
    assert sinks[1].thingNodeId == "i-i/B"
    assert sinks[1].name == "B - Next Object"


def test_blob_storage_hierarchy_node_create_structure_too_long_bucket_name() -> None:
    hierarchy_node = HierarchyNode(
        name="IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
        description="Super Category",
        substructure=[
            HierarchyNode(
                name="iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",
                description="Category",
                below_structure_defines_object_key=True,
                substructure=[
                    HierarchyNode(name="C", description="Subcategory"),
                ],
            ),
        ],
    )

    thing_nodes: list[StructureThingNode] = []
    bucket_names: list[StructureBucket] = []
    sinks: list[BlobStorageStructureSink] = []
    with pytest.raises(ValueError, match="to BucketName") as exc_info:
        hierarchy_node.create_structure(
            thing_nodes=thing_nodes,
            buckets=bucket_names,
            sinks=sinks,
            parent_id=None,
            part_of_bucket_name=True,
        )

    assert "Validation Error for transformation of" in str(exc_info.value)
    assert "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii-iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii" in str(
        exc_info.value
    )
    assert "to BucketName" in str(exc_info.value)


def test_blob_storage_models_find_duplicates() -> None:
    item_list = ["apple", "banana", "cherry", "apple", "banana"]
    duplicates = find_duplicates(item_list)

    assert len(duplicates) == 2
    assert "apple" in duplicates
    assert "banana" in duplicates


def test_blob_storage_class_adapter_hierarchy_happy_path() -> None:
    adapter_hierarchy = AdapterHierarchy(
        structure=[
            HierarchyNode(
                name="I",
                description="Super Category",
                substructure=[
                    HierarchyNode(
                        name="i",
                        description="Category",
                        below_structure_defines_object_key=True,
                        substructure=[
                            HierarchyNode(
                                name="A",
                                description="Subcategory",
                                substructure=[],
                            ),
                            HierarchyNode(
                                name="B",
                                description="Subcategory",
                                substructure=None,
                            ),
                            HierarchyNode(name="C", description="Subcategory"),
                            HierarchyNode(name="D", description="Subcategory"),
                        ],
                    ),
                    HierarchyNode(
                        name="ii",
                        description="Category",
                        below_structure_defines_object_key=True,
                        substructure=[
                            HierarchyNode(name="E", description="Subcategory")
                        ],
                    ),
                    HierarchyNode(
                        name="iii",
                        description="Category",
                        below_structure_defines_object_key=True,
                        substructure=[
                            HierarchyNode(name="F", description="Subcategory"),
                            HierarchyNode(name="G", description="Subcategory"),
                        ],
                    ),
                ],
            )
        ],
    )

    assert adapter_hierarchy.structure[0].get_depth() == 3
    assert adapter_hierarchy.structure[0].substructure is not None
    assert adapter_hierarchy.structure[0].substructure[0].get_depth() == 2
    assert adapter_hierarchy.structure[0].substructure[0].substructure is not None
    assert (
        adapter_hierarchy.structure[0].substructure[0].substructure[0].get_depth() == 1
    )

    thing_nodes = adapter_hierarchy.thing_nodes
    bucket_names = adapter_hierarchy.structure_buckets
    sinks = adapter_hierarchy.sinks

    assert len(thing_nodes) == 11
    assert len(bucket_names) == 3
    assert len(sinks) == 7

    hierarchy_from_file = AdapterHierarchy.from_file(
        "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
    )
    thing_nodes_from_file = hierarchy_from_file.thing_nodes
    bucket_names_from_file = hierarchy_from_file.structure_buckets
    sinks_from_file = hierarchy_from_file.sinks

    assert len(thing_nodes_from_file) == 14
    assert len(bucket_names_from_file) == 4
    assert len(sinks_from_file) == 8

    with pytest.raises(MissingHierarchyError):
        AdapterHierarchy.from_file("tests/data/blob_storage/not_there.json")


def test_blob_storage_class_adapter_hierarchy_with_non_positive_object_key_path() -> (
    None
):
    adapter_hierarchy = AdapterHierarchy(
        structure=(HierarchyNode(name="I", description=""),)
    )
    with pytest.raises(ValueError, match="Without an object key prefix") as exc_info:
        adapter_hierarchy.thing_nodes
    assert "Without an object key prefix no sinks or sources" in str(exc_info.value)


def test_blob_storage_class_adapter_hierarchy_with_name_invalid_error() -> None:
    structure = (
        HierarchyNode(
            name="IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII",
            description="Super Category",
            substructure=[
                HierarchyNode(
                    name="iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",
                    description="Category",
                    below_structure_defines_object_key=True,
                    substructure=[
                        HierarchyNode(name="C", description="Subcategory"),
                    ],
                ),
            ],
        ),
    )

    adapter_hierarchy = AdapterHierarchy(structure=structure)

    with pytest.raises(ValueError, match="to BucketName") as exc_info:
        adapter_hierarchy.structure_buckets

    assert "Validation Error for transformation of StructureThingNode " in str(
        exc_info.value
    )
    assert "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii-iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii" in str(
        exc_info.value
    )
    assert "to BucketName" in str(exc_info.value)


def test_blob_storage_adapter_hierarchy_identify_second_last_node_as_bucket_end() -> (
    None
):
    adapter_hierarchy = AdapterHierarchy(
        structure=(
            HierarchyNode(
                name="III",
                description="Super Category",
                substructure=[
                    HierarchyNode(
                        name="i",
                        description="Category",
                    ),
                ],
            ),
        )
    )

    assert adapter_hierarchy.structure_buckets[0].name == "iii"


def test_blob_storage_adapter_hierarchy_with_duplicates() -> None:
    adapter_hierarchy = AdapterHierarchy(
        structure=[
            HierarchyNode(
                name="III",
                description="Super Category",
                below_structure_defines_object_key=True,
                substructure=[
                    HierarchyNode(
                        name="i",
                        description="Category",
                    )
                ],
            ),
            HierarchyNode(
                name="iii",
                description="Super Category",
                below_structure_defines_object_key=True,
                substructure=[
                    HierarchyNode(
                        name="I",
                        description="Category",
                    )
                ],
            ),
        ],
    )
    with pytest.raises(ValueError, match="not unique") as exc_info:
        adapter_hierarchy.structure_buckets
    assert "The bucket names generated from the config file are not unique!" in str(
        exc_info.value
    )
