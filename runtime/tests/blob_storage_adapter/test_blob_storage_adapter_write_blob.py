import logging
from unittest import mock

import boto3
import pytest
from moto import mock_s3

from hetdesrun.adapters.blob_storage.models import BlobStorageStructureSink
from hetdesrun.adapters.blob_storage.write_blob import write_blob_to_storage


def test_blob_storage_write_blob_to_storage(caplog):
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        client_mock.create_bucket(Bucket="i-ii")
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
                        data=bytes(42), thing_node_id="i-ii/A", metadata_key="A - Next Object"
                    )
                    assert (
                        "Write data for sink 'i-ii/A_next' to storage "
                        "into bucket 'i-ii' as blob with key 'A_"
                    ) in caplog.text
