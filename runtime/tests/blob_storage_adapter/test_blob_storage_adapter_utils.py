import logging
from typing import List
from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNameInvalidError,
    ThingNodeInvalidError,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    BucketName,
    Category,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.utils import find_duplicates, walk_structure


def test_blob_storage_utils_walk_structure_happy_path():
    bucket_level = 2
    total_number_of_levels = 3
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
                        "substructure": [{"name": "E", "description": "Subcategory"}],
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
        )
    ]
    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []

    walk_structure(
        parent_id=None,
        tn_append_list=thing_nodes,
        bucket_append_list=bucket_names,
        snk_append_list=sinks,
        structure=structure,
        bucket_level=bucket_level,
        total_nof_levels=total_number_of_levels,
        level=1,
    )

    assert len(thing_nodes) == 11
    assert len(bucket_names) == 3
    assert len(sinks) == 7


@pytest.mark.skip("Error message not in log")
def test_blob_storage_utils_walk_structure_thing_node_invalid_error(caplog):
    bucket_level = 2
    total_number_of_levels = 3
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
    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []
    with caplog.at_level(logging.ERROR):
        caplog.clear()
        with mock.patch(
            "hetdesrun.adapters.blob_storage.models.Category.to_thing_node",
            side_effect=ThingNodeInvalidError,
        ):
            with pytest.raises(ThingNodeInvalidError):
                walk_structure(
                    parent_id=None,
                    tn_append_list=thing_nodes,
                    bucket_append_list=bucket_names,
                    snk_append_list=sinks,
                    structure=structure,
                    bucket_level=bucket_level,
                    total_nof_levels=total_number_of_levels,
                    level=1,
                )

        assert "ValidationError for transformation of category " in caplog.text


@pytest.mark.skip("ConstrainedStr does seem to not behave as expected")
def test_blob_storage_utils_walk_structure_bucket_name_invalid_error(caplog):
    bucket_level = 2
    total_number_of_levels = 3
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
    thing_nodes: List[StructureThingNode] = []
    bucket_names: List[BucketName] = []
    sinks: List[BlobStorageStructureSink] = []
    with caplog.at_level(logging.INFO):
        caplog.clear()
        with pytest.raises(BucketNameInvalidError):

            walk_structure(
                parent_id=None,
                tn_append_list=thing_nodes,
                bucket_append_list=bucket_names,
                snk_append_list=sinks,
                structure=structure,
                bucket_level=bucket_level,
                total_nof_levels=total_number_of_levels,
                level=1,
            )
        assert (
            "ValidationError for transformation of "
            "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii-iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii to BucketName"
        ) in caplog.text


def test_blob_storage_utils_get_setup_from_config():
    # TODO: implement test_blob_storage_utils_get_setup_from_config
    pass


def test_blob_storage_utils_find_duplicates():
    item_list = ["apple", "banana", "cherry", "apple", "banana"]
    duplicates = find_duplicates(item_list)

    assert len(duplicates) == 2
    assert "apple" in duplicates
    assert "banana" in duplicates


def test_blob_storage_utils_setup_adapter():
    # TODO: implement test_blob_storage_utils_setup_adapter
    pass
