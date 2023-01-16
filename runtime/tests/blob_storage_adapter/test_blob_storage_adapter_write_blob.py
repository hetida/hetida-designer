import logging
import struct
from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.models import BlobStorageStructureSink
from hetdesrun.adapters.blob_storage.write_blob import send_data, write_blob_to_storage
from hetdesrun.models.data_selection import FilteredSink


def test_blob_storage_write_blob_to_storage(caplog):
    with mock_s3():
        bucket_name = "i-ii"
        client_mock = boto3.client("s3", region_name="us-east-1")
        client_mock.create_bucket(Bucket=bucket_name)
        with mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
            return_value=client_mock,
        ):
            with mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSink(
                    id="i-ii/A_next",
                    thingNodeId="i-ii/A",
                    name="A - Next Object",
                    path="i-ii/A",
                    metadataKey="A - Next Object",
                ),
            ):
                with caplog.at_level(logging.INFO):
                    caplog.clear()
                    write_blob_to_storage(
                        data=struct.pack(">i", 42),
                        thing_node_id="i-ii/A",
                        metadata_key="A - Next Object",
                    )
                    assert (
                        "Write data for sink 'i-ii/A_next' to storage "
                        "into bucket 'i-ii' as blob with key 'A_"
                    ) in caplog.text

                    object_summaries_response = client_mock.list_objects_v2(
                        Bucket=bucket_name
                    )
                    assert object_summaries_response["KeyCount"] == 1
                    object_key = object_summaries_response["Contents"][0]["Key"]
                    object_response = client_mock.get_object(
                        Bucket=bucket_name, Key=object_key
                    )
                    assert struct.unpack(">i", object_response["Body"].read()) == (42,)


@pytest.mark.asyncio
async def test_blob_storage_send_data():
    with mock.patch(
        "hetdesrun.adapters.blob_storage.write_blob.write_blob_to_storage"
    ) as mocked_write_blob_to_storage:
        data = struct.pack(">i", 42)
        filtered_sink = FilteredSink(
            ref_id="i-ii/A",
            ref_id_type="SINK",
            ref_key="A - Next Object",
            type="Any",
        )
        await send_data(
            wf_output_name_to_filtered_sink_mapping_dict={"output_name": filtered_sink},
            wf_output_name_to_value_mapping_dict={"output_name": data},
            adapter_key="blob-storage-adapter"
        )
        assert mocked_write_blob_to_storage.call_count == 1
        _, args, _ = mocked_write_blob_to_storage.mock_calls[0]
        assert len(args) == 3
        assert args[0] == data
        assert args[1] == filtered_sink.ref_id
        assert args[2] == filtered_sink.ref_key
