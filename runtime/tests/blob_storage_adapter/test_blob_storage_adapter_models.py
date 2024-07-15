from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from hetdesrun.adapters.blob_storage import (
    IDENTIFIER_SEPARATOR,
)
from hetdesrun.adapters.blob_storage.exceptions import MissingHierarchyError
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BlobStorageStructureSource,
    FileExtension,
    HierarchyNode,
    IdString,
    ObjectKey,
    StructureBucket,
    StructureThingNode,
    find_duplicates,
    get_structure_bucket_and_object_key_prefix_from_id,
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
            name="very-long-bucket-name-that-is-longer-than-the-maximal-allowed-length-of-64-char"
        )


def test_blob_storage_class_object_key() -> None:
    with pytest.raises(ValueError, match="must have timezone UTC"):
        object_key = ObjectKey(
            string="A_2022-01-02T14:23:18+01:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
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
            file_extension=FileExtension.Pickle,
        )

    object_key = ObjectKey(
        string="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
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
        file_extension=FileExtension.Pickle,
    )

    assert (
        object_key.string == "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
    )
    assert object_key.name == "A"
    assert object_key.time == datetime(
        year=2022, month=1, day=2, hour=14, minute=23, second=18, tzinfo=timezone.utc
    )

    object_key_from_name = ObjectKey.from_name_and_job_id(
        IdString("B"),
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
        file_extension=FileExtension.H5,
    )

    object_key_from_name_and_time_and_job_id = ObjectKey.from_name_and_time_and_job_id(
        name=IdString("A"),
        time=datetime.fromisoformat("2022-01-02T14:23:18+00:00").replace(tzinfo=timezone.utc),
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
        file_extension=FileExtension.Pickle,
    )
    assert object_key_from_name_and_time_and_job_id.string == (
        "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
    )

    object_key_from_name_and_time_and_job_id_with_ext = ObjectKey.from_name_and_time_and_job_id(
        name=IdString("A"),
        time=datetime.fromisoformat("2022-01-02T14:23:18+00:00").replace(tzinfo=timezone.utc),
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
        file_extension=FileExtension.H5,
    )
    assert object_key_from_name_and_time_and_job_id_with_ext.string == (
        "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5"
    )

    object_key_from_string = ObjectKey.from_string(object_key_from_name.string)
    assert object_key_from_name == object_key_from_string

    object_key_from_string_with_extension = ObjectKey.from_string(
        IdString("A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5")
    )
    assert object_key_from_string_with_extension.file_extension == "h5"

    with pytest.raises(ValueError, match="must have timezone UTC"):
        object_key_from_string_with_extension = ObjectKey.from_string(
            IdString("A_2022-01-02T14:23:18+02:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5")
        )

    with pytest.raises(ValueError, match=f"contains '{IDENTIFIER_SEPARATOR}' less than"):
        ObjectKey.from_string(
            IdString("A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f")
        )

    object_key_from_thing_node_id_and_metadata_key = ObjectKey.from_thing_node_id_and_metadata_key(
        thing_node_id=IdString("i-ii/A"),
        metadata_key="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
    )
    assert (
        object_key_from_thing_node_id_and_metadata_key.string
        == "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
    )

    ok_from_thing_node_id_and_metadata_key_with_ext = ObjectKey.from_thing_node_id_and_metadata_key(
        thing_node_id=IdString("i-ii/A"),
        metadata_key="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
        file_extension=FileExtension.H5,
    )
    assert (
        ok_from_thing_node_id_and_metadata_key_with_ext.string
        == "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5"
    )

    with pytest.raises(ValueError, match="must have timezone UTC"):
        ObjectKey.from_thing_node_id_and_metadata_key(
            thing_node_id=IdString("i-ii/A"),
            metadata_key=(
                "A - 2022-01-02 14:23:18+02:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    thing_node_id_from_ok = object_key_from_thing_node_id_and_metadata_key.to_thing_node_id(
        bucket=StructureBucket(name="i-ii")
    )
    assert thing_node_id_from_ok == IdString("i-ii/A")


def test_blob_storage_class_structure_thing_node() -> None:
    StructureThingNode(id="i-ii", parentId="i", name="II", description="")
    StructureThingNode(id="i-ii/A", parentId="i-ii", name="A", description="")

    with pytest.raises(ValidationError, match="at least 1 characters"):
        # ThingNodeName shorter than min_length
        StructureThingNode(id="i-ii/A", name="", description="")

    with pytest.raises(ValidationError, match="at least 1 characters"):
        # IdString shorter than min_length
        StructureThingNode(id="", name="A", description="")

    with pytest.raises(ValidationError, match="does not match regex"):
        # ThingNodeName violates regex
        StructureThingNode(id="i-ii/A", name="ä", description="")

    with pytest.raises(ValidationError, match="does not match regex"):
        # IdString violates regex
        StructureThingNode(id="~", name="A", description="")

    with pytest.raises(ValidationError, match=r"at most.* characters"):
        # ThingNodeName longer than max_length
        StructureThingNode(
            id="i-ii/A",
            name="very-long-thing-node-name-that-is-longer-than-the-maximal-allowed-length-of-63-char",
            description="",
        )

    with pytest.raises(ValidationError, match=r"id.* must consist of.* parent id.* name"):
        # id does not consist of parentId and name combined with bucket name or object key separator
        StructureThingNode(id="i-ii/A", parentId="i-i", name="A", description="")


def test_blob_storage_class_structure_source_works() -> None:
    source = BlobStorageStructureSource(
        id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
        thingNodeId="i-ii/A",
        name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
        path="i-ii/A",
        metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
    )

    assert source.id == "i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
    assert source.thingNodeId == "i-ii/A"
    assert (
        source.name == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
    )
    assert source.path == "i-ii/A"
    assert (
        source.metadataKey
        == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
    )
    assert source.type == "metadata(any)"
    assert source.visible is True
    assert source.filters == {}

    (
        src_bucket,
        src_object_key_string,
    ) = get_structure_bucket_and_object_key_prefix_from_id(source.id)
    src_from_bkt_and_ok = BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=src_bucket, object_key=ObjectKey.from_string(src_object_key_string)
    )
    assert src_from_bkt_and_ok == source

    multi_level_ok_src = BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=StructureBucket(name="iii"),
        object_key=ObjectKey.from_string(
            IdString("x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl")
        ),
    )
    assert (
        multi_level_ok_src.id
        == "iii/x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
    )
    assert (
        multi_level_ok_src.name
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
    )
    assert multi_level_ok_src.thingNodeId == "iii/x/C"
    assert (
        multi_level_ok_src.metadataKey
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
    )
    assert multi_level_ok_src.path == "iii/x/C"

    src_with_ext_from_bkt_and_ok = BlobStorageStructureSource.from_structure_bucket_and_object_key(
        bucket=StructureBucket(name="iii"),
        object_key=ObjectKey.from_string(
            IdString("x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5")
        ),
    )
    assert (
        src_with_ext_from_bkt_and_ok.id
        == "iii/x/C_2023-02-08T16:48:58+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.h5"
    )
    assert (
        src_with_ext_from_bkt_and_ok.name
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (h5)"
    )
    assert src_with_ext_from_bkt_and_ok.thingNodeId == "iii/x/C"
    assert (
        src_with_ext_from_bkt_and_ok.metadataKey
        == "C - 2023-02-08 16:48:58+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (h5)"
    )
    assert src_with_ext_from_bkt_and_ok.path == "iii/x/C"


def test_blob_storage_class_structure_source_raises_exceptions() -> None:
    with pytest.raises(ValidationError, match=r"id.* does not contain"):
        # invalid id due to no object key dir separator
        BlobStorageStructureSource(
            id="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"first part.* of.* id.* correspond to.* bucket"):
        # invalid id due to bucket name part invalid
        BlobStorageStructureSource(
            id="I-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"second part.* of.* id.* correspond to.* object"):
        # invalid id due to object key part invalid
        BlobStorageStructureSource(
            id="i-ii/A2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"thing node id.* does not match.* id"):
        # thingNodeId does not match id
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/B",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"source name.* must contain"):
        # name invalid due to missing separator
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"source name.* start with.* name.* of.* thing node"):
        # name does not match id due to thing node name
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"time of.* name.* must match.* time in.* id"):
        # name does not match id due to timestamp
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A - 2023-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"path.* must be.* thingNodeId"):
        # path does not match thingNodeId
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/B",
            metadataKey=(
                "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
        )

    with pytest.raises(ValidationError, match=r"metadataKey.* must be.* name"):
        # metadataKey does not match name
        BlobStorageStructureSource(
            id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-ii/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-ii/A",
            metadataKey=(
                "B - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
            ),
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
    assert "object_key_suffix" in sink.filters

    snk_bucket, snk_object_key = sink.to_structure_bucket_and_object_key(
        job_id=UUID("4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"),
        file_extension=FileExtension.Pickle,
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

    with pytest.raises(ValidationError, match=r"id.* does not contain"):
        # invalid id due to no object key dir separator
        BlobStorageStructureSink(
            id="A_generic_sink",
            thingNodeId="A",
            name="A - Next Object",
            path="A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"first part.* of.* id.* correspond to.* bucket"):
        # invalid id due to bucket name part invalid
        BlobStorageStructureSink(
            id="I-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"sink id.* must end with"):
        # invalid id due to object key part invalid
        BlobStorageStructureSink(
            id="i-ii/Anext",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"thing node id.* match.* id"):
        # thingNodeId does not match id
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/B",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"sink name.* must contain"):
        # name invalid due to missing separator
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"sink name.* start with.* name.* of.* thing node"):
        # name does not match id due to thing node name
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="B - Next Object",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"sink name.* must end with"):
        # name does not match id due to timestamp
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Trained Model",
            path="i-ii/A",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"path.* must be.* thingNodeId"):
        # path does not match thingNodeId
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/B",
            metadataKey="A - Next Object",
        )

    with pytest.raises(ValidationError, match=r"metadataKey.* must be.* name"):
        # metadataKey does not match name
        BlobStorageStructureSink(
            id="i-ii/A_generic_sink",
            thingNodeId="i-ii/A",
            name="A - Next Object",
            path="i-ii/A",
            metadataKey="B - Next Object",
        )


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
        name="veryLongValidFirstPartOfBucketName",
        description="Super Category",
        substructure=[
            HierarchyNode(
                name="veryLongValid2ndPartOfBucketNameYieldingTooLongBucketName",
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
    with pytest.raises(ValueError, match="to BucketName"):
        hierarchy_node.create_structure(
            thing_nodes=thing_nodes,
            buckets=bucket_names,
            sinks=sinks,
            parent_id=None,
            part_of_bucket_name=True,
        )


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
                        substructure=[HierarchyNode(name="E", description="Subcategory")],
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
    assert adapter_hierarchy.structure[0].substructure[0].substructure[0].get_depth() == 1

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


def test_blob_storage_class_adapter_hierarchy_with_non_positive_object_key_path() -> None:
    adapter_hierarchy = AdapterHierarchy(structure=(HierarchyNode(name="I", description=""),))
    with pytest.raises(ValueError, match="Without an object key prefix"):
        adapter_hierarchy.thing_nodes  # noqa: B018


def test_blob_storage_class_adapter_hierarchy_with_name_invalid_error() -> None:
    structure = (
        HierarchyNode(
            name="veryLongValid1stPartOfBucketName",
            description="Super Category",
            substructure=[
                HierarchyNode(
                    name="veryLongValid2ndPartOfBucketNameYieldingTooLongBucketName",
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

    with pytest.raises(ValueError, match="to BucketName"):
        adapter_hierarchy.structure_buckets  # noqa: B018


def test_blob_storage_adapter_hierarchy_identify_second_last_node_as_bucket_end() -> None:
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
                        name="I",
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
                        description="Another Category",
                    )
                ],
            ),
        ],
    )
    with pytest.raises(ValueError, match="Bucket names are not unique"):
        adapter_hierarchy.structure_buckets  # noqa: B018

    adapter_hierarchy = AdapterHierarchy(
        structure=[
            HierarchyNode(
                name="III",
                description="Super Category",
                below_structure_defines_object_key=True,
                substructure=[
                    HierarchyNode(
                        name="I",
                        description="Category",
                    ),
                    HierarchyNode(
                        name="I",
                        description="Another Category",
                    ),
                ],
            ),
        ],
    )
    with pytest.raises(ValueError, match="Thing nodes are not unique"):
        adapter_hierarchy.structure_buckets  # noqa: B018
