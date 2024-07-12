import pickle
import struct
from io import BytesIO
from typing import Any
from unittest import mock

import boto3
import joblib
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.exceptions import (
    AdapterConnectionError,
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.load_blob import load_blob_from_storage, load_data
from hetdesrun.adapters.blob_storage.models import BlobStorageStructureSource
from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.models.data_selection import FilteredSource


@pytest.mark.asyncio
async def test_blob_storage_load_blob_from_storage_works(caplog: Any) -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        file_object = BytesIO()
        data = struct.pack(">i", 42)
        joblib.dump(data, file_object)
        file_object.seek(0)
        client_mock.create_bucket(Bucket=bucket_name)
        client_mock.put_object(
            Bucket=bucket_name,
            Key="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            Body=file_object.read(),
        )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",  # noqa: E501
                    path="i-ii/A",
                    metadataKey=(
                        "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                    ),
                ),
            ),
        ):
            blob = await load_blob_from_storage(
                thing_node_id="i-ii/A",
                metadata_key=(
                    "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                ),
            )

            assert struct.unpack(">i", blob) == (42,)


@pytest.mark.asyncio
async def test_blob_storage_load_blob_from_storage_with_non_existing_source() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        client_mock.put_object(
            Bucket=bucket_name,
            Key="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            Body=struct.pack(">i", 42),
        )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                side_effect=StructureObjectNotFound("Found no thing node"),
            ),
            pytest.raises(AdapterClientWiringInvalidError, match="Found no thing node"),
        ):
            await load_blob_from_storage(
                thing_node_id="i-ii/A",
                metadata_key="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            )


@pytest.mark.asyncio
async def test_blob_storage_load_blob_from_storage_with_non_existing_bucket() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        file_object = BytesIO()
        pickle.dump(42, file_object, protocol=pickle.HIGHEST_PROTOCOL)
        file_object.seek(0)
        client_mock.put_object(
            Bucket=bucket_name,
            Key="A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            Body=file_object,
        )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",  # noqa: E501
                    path="i-ii/A",
                    metadataKey=(
                        "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                    ),
                ),
            ),
        ):
            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.load_blob.ensure_bucket_exists",
                    side_effect=AdapterConnectionError,
                ),
                pytest.raises(AdapterConnectionError),
            ):
                await load_blob_from_storage(
                    thing_node_id="i-ii/A",
                    metadata_key=(
                        "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                    ),
                )

            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.ensure_bucket_exists",
                return_value=None,
            ):
                await load_blob_from_storage(
                    thing_node_id="i-ii/A",
                    metadata_key=(
                        "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                    ),
                )


@pytest.mark.asyncio
async def test_blob_storage_load_blob_from_storage_with_non_existing_object() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",  # noqa: E501
                    path="i-ii/A",
                    metadataKey=(
                        "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                    ),
                ),
            ),
            pytest.raises(AdapterConnectionError, match="contains no object with the key"),
        ):
            await load_blob_from_storage(
                thing_node_id="i-ii/A",
                metadata_key=(
                    "A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                ),
            )


@pytest.mark.asyncio
async def test_blob_storage_load_data_works() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.load_blob.load_blob_from_storage",
        return_value=struct.pack(">i", 42),
    ) as mocked_load_blob_from_storage:
        filtered_source = FilteredSource(
            ref_id="i-ii/A",
            ref_id_type="SOURCE",
            ref_key="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f",
            type="Any",
        )
        loaded_data = await load_data(
            wf_input_name_to_filtered_source_mapping_dict={"input_name": filtered_source},
            adapter_key="blob-storage-adapter",
        )
        assert mocked_load_blob_from_storage.call_count == 1
        _, args, _ = mocked_load_blob_from_storage.mock_calls[0]
        assert len(args) == 2
        assert args[0] == filtered_source.ref_id
        assert args[1] == filtered_source.ref_key
        assert "input_name" in loaded_data
        assert loaded_data["input_name"] == struct.pack(">i", 42)


@pytest.mark.asyncio
async def test_blob_storage_load_data_with_error() -> None:
    filtered_source = FilteredSource(
        ref_id="i-ii/A",
        ref_id_type="SOURCE",
        ref_key=None,
        type="Any",
    )
    with pytest.raises(AdapterClientWiringInvalidError):
        await load_data(
            wf_input_name_to_filtered_source_mapping_dict={"input_name": filtered_source},
            adapter_key="blob-storage-adapter",
        )
