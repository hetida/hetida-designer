from typing import List
from unittest import mock

from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    Category,
    IdString,
    StructureBucket,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.utils import create_sources


def mocked_get_oks_in_bucket(bucket_name: StructureBucket) -> List[IdString]:
    if bucket_name == "i-i":
        return [
            IdString("A_2022-01-02T14:23:18+00:00"),
            IdString("A_2022-01-02T14:57:31+00:00"),
            IdString("A_test"),
        ]
    if bucket_name == "i-ii":
        return [
            IdString("B_2022-01-02T14:25:56+00:00"),
            IdString("D_2022-03-08T17:23:18+00:00"),
            IdString("D_2022-04-02T13:28:29+00:00"),
        ]


def test_blob_storage_utils_create_sources():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_adapter_structure",
        return_value=AdapterHierarchy(
            structure=(
                Category(
                    name="I",
                    description="",
                    substructure=(Category(name="I", description=""),),
                ),
            ),
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.thing_nodes",
            new_callable=mock.PropertyMock,
            return_value=[
                StructureThingNode(
                    id="i-i/A", parentId="i-i", name="A", description="Category"
                ),
                StructureThingNode(
                    id="i-ii/B", parentId="i-ii", name="B", description="Category"
                ),
                StructureThingNode(
                    id="i-ii/C", parentId="i-ii", name="C", description="Category"
                ),
            ],
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.structure_buckets",
                new_callable=mock.PropertyMock,
                return_value=[
                    StructureBucket(name="i-i"),
                    StructureBucket(name="i-ii"),
                ],
            ):
                with mock.patch(
                    "hetdesrun.adapters.blob_storage.utils.get_object_key_strings_in_bucket",
                    new=mocked_get_oks_in_bucket,
                ):
                    sources = create_sources()
                    assert len(sources) == 3
                    assert sources[0].id == "i-i/A_2022-01-02T14:23:18+00:00"
                    assert sources[0].thingNodeId == "i-i/A"
                    assert sources[0].name == "A - 2022-01-02 14:23:18+00:00"
                    assert sources[1].id == "i-i/A_2022-01-02T14:57:31+00:00"
                    assert sources[1].thingNodeId == "i-i/A"
                    assert sources[1].name == "A - 2022-01-02 14:57:31+00:00"
                    assert sources[2].id == "i-ii/B_2022-01-02T14:25:56+00:00"
                    assert sources[2].thingNodeId == "i-ii/B"
                    assert sources[2].name == "B - 2022-01-02 14:25:56+00:00"
