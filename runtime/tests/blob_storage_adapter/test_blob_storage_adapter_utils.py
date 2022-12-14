import logging
from typing import List
from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.models import (
    BucketName,
    IdString,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.utils import create_sources


def mocked_adapter() -> List[StructureThingNode]:
    return (
        [
            StructureThingNode(
                id="i/A", parent_id="i", name="A", description="Category"
            ),
            StructureThingNode(
                id="ii/B", parent_id="ii", name="B", description="Category"
            ),
            StructureThingNode(
                id="ii/C", parent_id="ii", name="C", description="Category"
            ),
        ],
    )


def mocked_bucket_names() -> List[BucketName]:
    return [BucketName("i"), BucketName("ii")]


def mocked_get_oks_in_bucket(bucket_name: BucketName) -> List[IdString]:
    if bucket_name == "i":
        return [
            IdString("A_2022-01-02T14:23:18+00:00"),
            IdString("A_2022-01-02T14:57:31+00:00"),
        ]
    if bucket_name == "ii":
        return [
            IdString("B_2022-01-02T14:25:56+00:00"),
            IdString("D_2022-03-08T17:23:18+00:00"),
            IdString("D_2022-04-02T13:28:29+00:00"),
        ]


def test_blob_storage_utils_create_sources():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.thing_nodes",
        new_callable=mock.PropertyMock,
        return_value=[
            StructureThingNode(
                id="i/A", parentId="i", name="A", description="Category"
            ),
            StructureThingNode(
                id="ii/B", parentId="ii", name="B", description="Category"
            ),
            StructureThingNode(
                id="ii/C", parentId="ii", name="C", description="Category"
            ),
        ],
    ):
        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.bucket_names",
            new_callable=mock.PropertyMock,
            return_value=[BucketName("i"), BucketName("ii")],
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.utils.get_object_key_strings_in_bucket",
                new=mocked_get_oks_in_bucket,
            ):
                sources = create_sources()
                assert len(sources) == 3
                assert sources[0].id == "i/A_2022-01-02T14:23:18+00:00"
                assert sources[0].thingNodeId == "i/A"
                assert sources[0].name == "A - 2022-01-02 14:23:18+00:00"
                assert sources[1].id == "i/A_2022-01-02T14:57:31+00:00"
                assert sources[1].thingNodeId == "i/A"
                assert sources[1].name == "A - 2022-01-02 14:57:31+00:00"
                assert sources[2].id == "ii/B_2022-01-02T14:25:56+00:00"
                assert sources[2].thingNodeId == "ii/B"
                assert sources[2].name == "B - 2022-01-02 14:25:56+00:00"
