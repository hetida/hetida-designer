from unittest import mock

import pytest

from hetdesrun.adapters.blob_storage.exceptions import StructureObjectNotFound
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    HierarchyNode,
    IdString,
    StructureBucket,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.utils import (
    get_all_sources_from_buckets_and_object_keys,
    get_source_by_id_from_bucket_and_object_key,
    get_sources_by_parent_id_from_bucket_and_object_keys,
)


async def mocked_get_oks_in_bucket(bucket_name: StructureBucket) -> list[IdString]:
    if bucket_name == "i-i":
        return [
            IdString(
                "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
            ),
            IdString(
                "A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
            ),
            IdString("A_test"),
        ]
    if bucket_name == "i-ii":
        return [
            IdString(
                "B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
            ),
            IdString(
                "D_2022-03-08T17:23:18+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa"
            ),
            IdString(
                "D_2022-04-02T13:28:29+00:00_af77087b-a064-4ff9-9c4a-d23b2c503ade"
            ),
        ]
    raise ValueError("bucket_name must be 'i-i' or 'i-ii'!")


@pytest.mark.asyncio
async def test_blob_storage_utils_get_all_sources_from_buckets_and_object_keys() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_adapter_structure",
        return_value=AdapterHierarchy(
            structure=(
                HierarchyNode(
                    name="I",
                    description="",
                    substructure=(HierarchyNode(name="I", description=""),),
                ),
            ),
        ),
    ), mock.patch(
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
    ), mock.patch(
        "hetdesrun.adapters.blob_storage.models.AdapterHierarchy.structure_buckets",
        new_callable=mock.PropertyMock,
        return_value=[
            StructureBucket(name="i-i"),
            StructureBucket(name="i-ii"),
        ],
    ), mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_object_key_strings_in_bucket",
        new=mocked_get_oks_in_bucket,
    ):
        sources = await get_all_sources_from_buckets_and_object_keys()
        assert len(sources) == 3
        assert (
            sources[0].id
            == "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )
        assert sources[0].thingNodeId == "i-i/A"
        assert (
            sources[0].name
            == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )
        assert (
            sources[1].id
            == "i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert sources[1].thingNodeId == "i-i/A"
        assert (
            sources[1].name
            == "A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43"
        )
        assert (
            sources[2].id
            == "i-ii/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
        )
        assert sources[2].thingNodeId == "i-ii/B"
        assert (
            sources[2].name
            == "B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
        )


@pytest.mark.asyncio
async def test_blob_storage_utils_get_source_by_id_from_bucket_and_object_key() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_adapter_structure",
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
    ), mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_object_key_strings_in_bucket",
        new=mocked_get_oks_in_bucket,
    ):
        source_id = IdString(
            "i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )

        source = await get_source_by_id_from_bucket_and_object_key(source_id)

        assert (
            source.name
            == "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f"
        )

        source_id_without_bucket = IdString(
            "i-ii/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
        )
        with pytest.raises(StructureObjectNotFound, match="no bucket"):
            await get_source_by_id_from_bucket_and_object_key(source_id_without_bucket)

        source_id_without_object_key = IdString(
            "i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51"
        )
        with pytest.raises(StructureObjectNotFound, match="no object"):
            await get_source_by_id_from_bucket_and_object_key(
                source_id_without_object_key
            )


@pytest.mark.asyncio
async def test_blob_storage_utils_get_sources_by_parent_id_from_bucket_and_object_keys() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_adapter_structure",
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
    ), mock.patch(
        "hetdesrun.adapters.blob_storage.utils.get_object_key_strings_in_bucket",
        new=mocked_get_oks_in_bucket,
    ):
        parent_id = IdString("i-i/A")
        sources_from_parent_id = (
            await get_sources_by_parent_id_from_bucket_and_object_keys(parent_id)
        )

        assert len(sources_from_parent_id) == 2

        too_high_parent_id = IdString("i-i")
        sources_from_too_high_parent_id = (
            await get_sources_by_parent_id_from_bucket_and_object_keys(
                too_high_parent_id
            )
        )

        assert len(sources_from_too_high_parent_id) == 0

        parent_id_without_bucket = IdString("i-ii/A")
        with pytest.raises(StructureObjectNotFound, match="no bucket"):
            await get_sources_by_parent_id_from_bucket_and_object_keys(
                parent_id_without_bucket
            )
