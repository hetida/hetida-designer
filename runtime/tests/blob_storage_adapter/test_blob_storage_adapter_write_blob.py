import struct
from io import BytesIO
from unittest import mock
from uuid import UUID

import boto3
import joblib
import pytest
from botocore.exceptions import ClientError
from moto import mock_s3

from hetdesrun.adapters.blob_storage.exceptions import (
    AdapterConnectionError,
    StructureObjectNotFound,
)
from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSink,
    BucketName,
    FileExtension,
    IdString,
    ObjectKey,
    StructureBucket,
    StructureThingNode,
)
from hetdesrun.adapters.blob_storage.write_blob import (
    get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key,
    send_data,
    write_blob_to_storage,
    write_custom_objects_to_storage,
)
from hetdesrun.adapters.exceptions import AdapterClientWiringInvalidError
from hetdesrun.models.data_selection import FilteredSink


def test_blob_storage_get_sink_and_bucket_and_ok_from_thing_node_and_metadata_key() -> None:
    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy.from_file("demodata/blob_storage_adapter_hierarchy.json"),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
            return_value={"currently_executed_job_id": "1681ea7e-c57f-469a-ac12-592e3e8665cf"},
        ),
    ):
        (
            sink,
            bucket,
            ok,
        ) = get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
            thing_node_id="plantb/PicklingUnit/Outfeed/Anomalies",
            metadata_key="Anomalies - Next Object",
            file_extension=FileExtension.H5,
        )
        assert str(sink.id) == "plantb/PicklingUnit/Outfeed/Anomalies_generic_sink"
        assert str(bucket.name) == "plantb"
        assert ok.file_extension == "h5"
        assert ok.string.endswith("h5")

        # deterministic metadata key
        (
            sink,
            bucket,
            ok,
        ) = get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
            thing_node_id="plantb/PicklingUnit/Outfeed/Anomalies",
            metadata_key=(
                "Anomalies - 2023-03-23 10:16:25+00:00 - 1681ea7e-c57f-469a-ac12-592e3e8665cf"
            ),
            file_extension=FileExtension.H5,
        )
        assert str(sink.id) == "plantb/PicklingUnit/Outfeed/Anomalies_generic_sink"
        assert str(bucket.name) == "plantb"
        assert ok.file_extension == "h5"
        assert ok.string == (
            "PicklingUnit/Outfeed/Anomalies_2023-03-23T10:16:25+00:00"
            "_1681ea7e-c57f-469a-ac12-592e3e8665cf.h5"
        )

        with pytest.raises(AdapterClientWiringInvalidError, match="no thing node"):
            get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
                thing_node_id="plntb/PicklingUnit/Outfeed/Anomalies",  # misspelled bucket name
                metadata_key=(
                    "Anomalies - 2023-03-23 10:16:25+00:00 - 1681ea7e-c57f-469a-ac12-592e3e8665cf"
                ),
                file_extension=FileExtension.H5,
            )

        with pytest.raises(AdapterClientWiringInvalidError, match="not possible to generate"):
            get_sink_and_bucket_and_object_key_from_thing_node_and_metadata_key(
                thing_node_id="plantb/PicklingUnit/Outfeed/Anomalies",
                metadata_key=(
                    "Anomalies - 2023-03-23 10:16:25+00:00"  # missing job id
                ),
                file_extension=FileExtension.H5,
            )


@pytest.mark.asyncio
async def test_blob_storage_custom_objects_to_storage_works() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with mock.patch(
            "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
            return_value=client_mock,
        ):
            await write_custom_objects_to_storage(
                s3_client=client_mock,
                custom_objects={"key": {"value": 23}},
                structure_bucket=StructureBucket(name=BucketName(bucket_name)),
                object_key=ObjectKey.from_name_and_job_id(
                    name=IdString("E"),
                    job_id=UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4"),
                    file_extension=FileExtension.Pickle,
                ),
            )

            object_summaries_response = client_mock.list_objects_v2(Bucket=bucket_name)
            assert object_summaries_response["KeyCount"] == 1
            object_key = object_summaries_response["Contents"][0]["Key"]
            object_response = client_mock.get_object(Bucket=bucket_name, Key=object_key)
            pickled_data_bytes = object_response["Body"].read()
            file_object = BytesIO(pickled_data_bytes)
            loaded_object = joblib.load(file_object)
            assert loaded_object == {"key": {"value": 23}}


@pytest.mark.asyncio
async def test_blob_storage_custom_objects_to_storage_with_unexpected_error() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.put_object",
                side_effect=ClientError(error_response={"Error": {"Code": 404}}, operation_name=""),
            ),
            pytest.raises(AdapterConnectionError, match=r"Unexpected ClientError.*put_object"),
        ):
            await write_custom_objects_to_storage(
                s3_client=client_mock,
                custom_objects={"key": {"value": 23}},
                structure_bucket=StructureBucket(name=bucket_name),
                object_key=ObjectKey.from_name_and_job_id(
                    name=IdString("E"),
                    job_id=UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4"),
                    file_extension=FileExtension.Pickle,
                ),
            )


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_works() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSink(
                    id="i-ii/E_generic_sink",
                    thingNodeId="i-ii/E",
                    name="E - Next Object",
                    path="i-ii/E",
                    metadataKey="E - Next Object",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
        ):
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/E",
                metadata_key="E - Next Object",
                filters={},
            )

            object_summaries_response = client_mock.list_objects_v2(Bucket=bucket_name)
            assert object_summaries_response["KeyCount"] == 1
            object_key = object_summaries_response["Contents"][0]["Key"]
            object_response = client_mock.get_object(Bucket=bucket_name, Key=object_key)
            pickled_data_bytes = object_response["Body"].read()
            file_object = BytesIO(pickled_data_bytes)
            assert struct.unpack(">i", joblib.load(file_object)) == (42,)


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_unexpected_put_object_error() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSink(
                    id="i-ii/E_generic_sink",
                    thingNodeId="i-ii/E",
                    name="E - Next Object",
                    path="i-ii/E",
                    metadataKey="E - Next Object",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.put_object",
                side_effect=ClientError(error_response={"Error": {"Code": 404}}, operation_name=""),
            ),
            pytest.raises(AdapterConnectionError, match=r"Unexpected ClientError.*put_object"),
        ):
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/E",
                metadata_key="E - Next Object",
                filters={},
            )


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_unexpected_head_object_error() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        client_mock.head_object = mock.Mock(
            side_effect=ClientError(error_response={"Error": {"Code": 404}}, operation_name="")
        )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSink(
                    id="i-ii/E_generic_sink",
                    thingNodeId="i-ii/E",
                    name="E - Next Object",
                    path="i-ii/E",
                    metadataKey="E - Next Object",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
            pytest.raises(AdapterConnectionError, match=r"Unexpected ClientError.*head_object"),
        ):
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/E",
                metadata_key="E - Next Object",
                filters={},
            )


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_non_existing_sink() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                side_effect=StructureObjectNotFound("SinkNotFound message"),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_thing_node_by_id",
                return_value=StructureThingNode(
                    id="i-ii/E",
                    parentId="i-ii",
                    name="E",
                    description="",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
        ):
            thing_node_id = "i-ii/E"
            metadata_key = (
                "E - 2001-02-03 04:05:06+00:00 - " "e54d527d-70c7-4ac7-8b67-7aa8ec7b5ebe (pkl)"
            )
            await write_blob_to_storage(
                data=struct.pack(">i", 23),
                thing_node_id=thing_node_id,
                metadata_key=metadata_key,
                filters={},
            )

            object_summaries_response = client_mock.list_objects_v2(Bucket=bucket_name)
            assert object_summaries_response["KeyCount"] == 1
            object_key_string = object_summaries_response["Contents"][0]["Key"]
            assert (
                object_key_string
                == "E_2001-02-03T04:05:06+00:00_e54d527d-70c7-4ac7-8b67-7aa8ec7b5ebe.pkl"
            )
            object_response = client_mock.get_object(Bucket=bucket_name, Key=object_key_string)
            pickled_data_bytes = object_response["Body"].read()
            file_object = BytesIO(pickled_data_bytes)
            assert struct.unpack(">i", joblib.load(file_object)) == (23,)

            non_utc_metadata_key = (
                "E - 2001-02-03 04:05:06+02:00 - " "e54d527d-70c7-4ac7-8b67-7aa8ec7b5ebe (pkl)"
            )
            with pytest.raises(AdapterClientWiringInvalidError):
                await write_blob_to_storage(
                    data=struct.pack(">i", 23),
                    thing_node_id=thing_node_id,
                    metadata_key=non_utc_metadata_key,
                    filters={},
                )


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_non_existing_bucket() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                return_value=BlobStorageStructureSink(
                    id="i-ii/A_generic_sink",
                    thingNodeId="i-ii/A",
                    name="A - Next Object",
                    path="i-ii/A",
                    metadataKey="A - Next Object",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
        ):
            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.write_blob.ensure_bucket_exists",
                    side_effect=AdapterConnectionError,
                ),
                pytest.raises(AdapterConnectionError),
            ):
                await write_blob_to_storage(
                    data=struct.pack(">i", 42),
                    thing_node_id="i-ii/A",
                    metadata_key="A - Next Object",
                    filters={},
                )

            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/A",
                metadata_key="A - Next Object",
                filters={},
            )
            client_mock.head_bucket(Bucket="i-ii")


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_existing_object() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        object_key_string = "A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl"
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
                    id="i-ii/A_generic_sink",
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
            with (
                mock.patch(
                    "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                    return_value=mocked_sink,
                ),
                mock.patch(
                    "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                    return_value={
                        "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                    },
                ),
                pytest.raises(AdapterConnectionError),
            ):
                await write_blob_to_storage(
                    data=struct.pack(">i", 42),
                    thing_node_id="i-ii/A",
                    metadata_key="A - Next Object",
                    filters={},
                )


@pytest.mark.asyncio
async def test_blob_storage_write_blob_to_storage_with_object_key_suffix_filter() -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        bucket_name = "i-ii"
        client_mock.create_bucket(Bucket=bucket_name)
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_sink_by_thing_node_id_and_metadata_key",
                side_effect=StructureObjectNotFound,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_thing_node_by_id",
                return_value=StructureThingNode(
                    id="i-ii/E",
                    parentId="i-ii",
                    name="E",
                    description="",
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob._get_job_id_context",
                return_value={
                    "currently_executed_job_id": UUID("8c71d5e1-dbf7-4a18-9c94-930a51f0bdf4")
                },
            ),
        ):
            await write_blob_to_storage(
                data=struct.pack(">i", 42),
                thing_node_id="i-ii/E",
                metadata_key="E - Next Object",
                filters={
                    "object_key_suffix": (
                        "1970-01-01 00:00:00+00:00 - e411fabb-50fd-4262-855e-7a59e13bbfa3"
                    )
                },
            )

            object_summaries_response = client_mock.list_objects_v2(Bucket=bucket_name)
            assert object_summaries_response["KeyCount"] == 1
            object_key = object_summaries_response["Contents"][0]["Key"]
            assert (
                object_key == "E_1970-01-01T00:00:00+00:00_e411fabb-50fd-4262-855e-7a59e13bbfa3.pkl"
            )
            object_response = client_mock.get_object(Bucket=bucket_name, Key=object_key)
            pickled_data_bytes = object_response["Body"].read()
            file_object = BytesIO(pickled_data_bytes)
            assert struct.unpack(">i", joblib.load(file_object)) == (42,)

            with pytest.raises(
                AdapterClientWiringInvalidError, match=r"object_key_suffix.*invalid"
            ):
                await write_blob_to_storage(
                    data=struct.pack(">i", 42),
                    thing_node_id="i-ii/E",
                    metadata_key="E - Next Object",
                    filters={
                        "object_key_suffix": (
                            "1970-01-01 00:00:00 - e411fabb-50fd-4262-855e-7a59e13bbfa3"
                        )
                    },
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
        assert len(args) == 4
        assert args[0] == data
        assert args[1] == filtered_sink.ref_id
        assert args[2] == filtered_sink.ref_key
        assert args[3] == filtered_sink.filters


@pytest.mark.asyncio
async def test_blob_storage_send_data_with_invalid_wiring_error() -> None:
    data = struct.pack(">i", 42)
    filtered_sink = FilteredSink(
        ref_id=None,
        ref_id_type="SINK",
        ref_key="A - Next Object",
        type="Any",
    )

    with pytest.raises(AdapterClientWiringInvalidError):
        await send_data(
            wf_output_name_to_filtered_sink_mapping_dict={"output_name": filtered_sink},
            wf_output_name_to_value_mapping_dict={"output_name": data},
            adapter_key="blob-storage-adapter",
        )
