import logging
import struct
from io import BytesIO
from unittest import mock

import boto3
import joblib
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.exceptions import (
    AdapterConnectionError,
    StructureObjectNotFound,
    StructureObjectNotUnique,
)
from hetdesrun.adapters.blob_storage.models import (
    BlobStorageStructureSink,
    IdString,
    ObjectKey,
    StructureBucket,
)
from hetdesrun.adapters.blob_storage.write_blob import send_data, write_blob_to_storage
from hetdesrun.models.data_selection import FilteredSink


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_works(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
            return_value=client_mock,
        ), mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
            return_value=BlobStorageStructureSink(
                id="i-ii/A_next",
                thingNodeId="i-ii/A",
                name="A - Next Object",
                path="i-ii/A",
                metadataKey="A - Next Object",
            ),
        ), caplog.at_level(
            logging.INFO
        ):
            caplog.clear()
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/A",
                metadata_key="A - Next Object",
            )
            assert (
                "Write data for sink 'i-ii/A_next' to storage "
                "into bucket 'i-ii' as blob with key 'A_"
            ) in caplog.text

            object_summaries_response = client_mock.list_objects_v2(Bucket=bucket_name)
            assert object_summaries_response["KeyCount"] == 1
            object_key = object_summaries_response["Contents"][0]["Key"]
            object_response = client_mock.get_object(Bucket=bucket_name, Key=object_key)
            pickled_data_bytes = object_response["Body"].read()
            file_object = BytesIO(pickled_data_bytes)
            assert struct.unpack(">i", joblib.load(file_object)) == (42,)


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_non_existing_sink() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
        side_effect=StructureObjectNotFound("SinkNotFound message"),
    ):
        with pytest.raises(StructureObjectNotFound) as exc_info:
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/A",
                metadata_key="A - Next Object",
            )
        assert "SinkNotFound message" in str(exc_info.value)


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_multiple_existing_sinks() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
        side_effect=StructureObjectNotUnique("SinkNotUnique message"),
    ):
        with pytest.raises(StructureObjectNotUnique) as exc_info:
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/A",
                metadata_key="A - Next Object",
            )
        assert "SinkNotUnique message" in str(exc_info.value)


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_non_existing_bucket() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        with mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
            return_value=client_mock,
        ), mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
            return_value=BlobStorageStructureSink(
                id="i-ii/A_next",
                thingNodeId="i-ii/A",
                name="A - Next Object",
                path="i-ii/A",
                metadataKey="A - Next Object",
            ),
        ):
            with pytest.raises(AdapterConnectionError) as exc_info:
                await write_blob_to_storage(
                    data=struct.pack(">i", 42),
                    thing_node_id="i-ii/A",
                    metadata_key="A - Next Object",
                )
            assert "The bucket 'i-ii' does not exist!" in str(exc_info.value)


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_existing_object() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        object_key_string = "A_2022-01-02T14:23:18+00:00"
        client_mock.put_object(
            Bucket=bucket_name,
            Key=object_key_string,
            Body=struct.pack(">i", 42),
        )
        with mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
            return_value=client_mock,
        ):
            mocked_sink = mock.Mock(
                return_value=BlobStorageStructureSink(
                    id="i-ii/A_next",
                    thingNodeId="i-ii/A",
                    name="A - Next Object",
                    path="i-ii/A",
                    metadataKey="A - Next Object",
                )
            )
            mocked_sink.to_structure_bucket_and_object_key.return_value = (
                StructureBucket(name=bucket_name),
                ObjectKey.from_string(IdString(object_key_string)),
            )
            with mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=mocked_sink,
            ), pytest.raises(AdapterConnectionError):
                await write_blob_to_storage(
                    data=struct.pack(">i", 42),
                    thing_node_id="i-ii/A",
                    metadata_key="A - Next Object",
                )


@pytest.mark.asyncio
async def test_blob_storage_send_data_works() -> None:
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
            adapter_key="blob-storage-adapter",
        )
        assert mocked_write_blob_to_storage.call_count == 1
        _, args, _ = mocked_write_blob_to_storage.mock_calls[0]
        assert len(args) == 3
        assert args[0] == data
        assert args[1] == filtered_sink.ref_id
        assert args[2] == filtered_sink.ref_key


@pytest.mark.asyncio
async def test_blob_storage_send_data_with_error() -> None:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.write_blob.write_blob_to_storage",
        side_effect=AdapterConnectionError("Error message"),
    ):
        data = struct.pack(">i", 42)
        filtered_sink = FilteredSink(
            ref_id="i-ii/A",
            ref_id_type="SINK",
            ref_key="A - Next Object",
            type="Any",
        )
        with pytest.raises(AdapterConnectionError) as exc_info:
            await send_data(
                wf_output_name_to_filtered_sink_mapping_dict={
                    "output_name": filtered_sink
                },
                wf_output_name_to_value_mapping_dict={"output_name": data},
                adapter_key="blob-storage-adapter",
            )
        assert "Error message" in str(exc_info.value)
