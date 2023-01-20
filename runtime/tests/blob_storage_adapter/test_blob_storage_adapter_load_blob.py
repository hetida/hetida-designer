import logging
import struct
from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.exceptions import (
    BucketNotFound,
    ObjectNotFound,
    SourceNotFound,
    SourceNotUnique,
)
from hetdesrun.adapters.blob_storage.load_blob import load_blob_from_storage, load_data
from hetdesrun.adapters.blob_storage.models import BlobStorageStructureSource
from hetdesrun.models.data_selection import FilteredSource


def test_blob_storage_load_blob_from_storage(caplog):
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        client_mock.put_object(
            Bucket=bucket_name,
            Key="A_2022-01-02T14:23:18+00:00",
            Body=struct.pack(">i", 42),
        )
        with mock.patch(
            "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
            return_value=client_mock,
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00",
                    path="i-ii/A",
                    metadataKey="A - 2022-01-02 14:23:18+00:00",
                ),
            ):
                with caplog.at_level(logging.INFO):
                    caplog.clear()
                    blob = load_blob_from_storage(
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )
                    assert (
                        "Load data for source 'i-ii/A_2022-01-02T14:23:18+00:00' from storage "
                        "in bucket 'i-ii' under object key 'A_2022-01-02T14:23:18+00:00"
                    ) in caplog.text

                    assert struct.unpack(">i", blob) == (42,)

            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                side_effect=SourceNotFound("SourceNotFound message"),
            ):
                with pytest.raises(SourceNotFound) as exc_info:
                    load_blob_from_storage(
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )

                assert "SourceNotFound message" in str(exc_info.value)

            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                side_effect=SourceNotUnique("SourceNotUnique message"),
            ):
                with pytest.raises(SourceNotUnique) as exc_info:
                    load_blob_from_storage(
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )

                assert ("SourceNotUnique message") in str(exc_info.value)

    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        with mock.patch(
            "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
            return_value=client_mock,
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00",
                    path="i-ii/A",
                    metadataKey="A - 2022-01-02 14:23:18+00:00",
                ),
            ):
                with pytest.raises(BucketNotFound) as exc_info:
                    load_blob_from_storage(
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )
                assert "The bucket 'i-ii' does not exist!" in str(exc_info.value)

    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with mock.patch(
            "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
            return_value=client_mock,
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_source_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSource(
                    id="i-ii/A_2022-01-02T14:23:18+00:00",
                    thingNodeId="i-ii/A",
                    name="A - 2022-01-02 14:23:18+00:00",
                    path="i-ii/A",
                    metadataKey="A - 2022-01-02 14:23:18+00:00",
                ),
            ):
                with pytest.raises(ObjectNotFound) as exc_info:
                    load_blob_from_storage(
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )
                assert (
                    "The bucket 'i-ii' contains no object with "
                    "the key 'A_2022-01-02T14:23:18+00:00'"
                ) in str(exc_info.value)


@pytest.mark.asyncio
async def test_blob_storage_load_data():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.load_blob.load_blob_from_storage",
        return_value=struct.pack(">i", 42),
    ) as mocked_load_blob_from_storage:
        filtered_source = FilteredSource(
            ref_id="i-ii/A",
            ref_id_type="SINK",
            ref_key="A - Next Object",
            type="Any",
        )
        loaded_data = await load_data(
            wf_input_name_to_filtered_source_mapping_dict={
                "input_name": filtered_source
            },
            adapter_key="blob-storage-adapter",
        )
        assert mocked_load_blob_from_storage.call_count == 1
        _, args, _ = mocked_load_blob_from_storage.mock_calls[0]
        assert len(args) == 2
        assert args[0] == filtered_source.ref_id
        assert args[1] == filtered_source.ref_key
        assert "input_name" in loaded_data
        assert loaded_data["input_name"] == struct.pack(">i", 42)

    with mock.patch(
        "hetdesrun.adapters.blob_storage.load_blob.load_blob_from_storage",
        side_effect=ObjectNotFound("Error message"),
    ) as mocked_load_blob_from_storage:
        with pytest.raises(ObjectNotFound) as exc_info:
            await load_data(
                wf_input_name_to_filtered_source_mapping_dict={
                    "input_name": filtered_source
                },
                adapter_key="blob-storage-adapter",
            )
        assert "Error message" in str(exc_info.value)
