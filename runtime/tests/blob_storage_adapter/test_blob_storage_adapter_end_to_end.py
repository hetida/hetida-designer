import json
import os
import pickle
import struct
from io import BytesIO
from typing import Any
from unittest import mock

import boto3
import pytest
from httpx import AsyncClient
from moto import mock_s3

from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
)


async def run_workflow_with_client(
    workflow_json: dict, open_async_test_client: AsyncClient
) -> tuple[int, Any]:
    response = await open_async_test_client.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


@pytest.mark.asyncio
async def test_load_object_with_self_defined_class(
    async_test_client_with_blob_storage_adapter: AsyncClient,
) -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        client_mock.create_bucket(Bucket="i-i")
        client_mock.create_bucket(
            Bucket="i-ii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        client_mock.create_bucket(
            Bucket="i-iii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        client_mock.create_bucket(
            Bucket="iii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
                return_value=AdapterHierarchy.from_file(
                    "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
                return_value=AdapterHierarchy.from_file(
                    "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.service.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
        ):
            async with async_test_client_with_blob_storage_adapter as client:
                with open(
                    os.path.join(
                        "tests",
                        "data",
                        "store_object_with_class_wf_execution_input.json",
                    ),
                    encoding="utf8",
                ) as f:
                    loaded_store_object_workflow_exe_input = json.load(f)
                (
                    store_response_status_code,
                    store_response_json,
                ) = await run_workflow_with_client(loaded_store_object_workflow_exe_input, client)

                assert store_response_status_code == 200
                assert store_response_json["result"] == "ok"

                with open(
                    os.path.join(
                        "tests",
                        "data",
                        "load_object_with_class_wf_execution_input.json",
                    ),
                    encoding="utf8",
                ) as f:
                    loaded_load_object_workflow_exe_input = json.load(f)

                parent_id = loaded_load_object_workflow_exe_input["workflow_wiring"][
                    "input_wirings"
                ][0]["ref_id"]

                structure_response = await client.get(
                    f"/adapters/blob/structure?parentId={parent_id}"
                )
                assert structure_response.status_code == 200

                metadata_key = structure_response.json()["sources"][0]["metadataKey"]

                loaded_load_object_workflow_exe_input["workflow_wiring"]["input_wirings"][0][
                    "ref_key"
                ] = metadata_key

                (
                    load_response_status_code,
                    load_response_json,
                ) = await run_workflow_with_client(loaded_load_object_workflow_exe_input, client)

                assert load_response_status_code == 200
                assert load_response_json["result"] == "ok"


@pytest.mark.asyncio
async def test_store_object_under_key_which_already_exists(
    async_test_client_with_blob_storage_adapter: AsyncClient,
) -> None:
    with mock_s3():
        client_mock = boto3.client("s3", region_name="us-east-1")
        client_mock.create_bucket(Bucket="i-i")
        client_mock.create_bucket(
            Bucket="i-ii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        client_mock.create_bucket(
            Bucket="i-iii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        client_mock.create_bucket(
            Bucket="iii"
        )  # needed for get_all_sources_from_buckets_and_object_keys based on adapter structure
        file_object = BytesIO()
        data = struct.pack(">i", 42)
        pickle.dump(data, file_object)
        file_object.seek(0)
        client_mock.create_bucket(Bucket="i-i")
        client_mock.put_object(
            Bucket="i-i",
            Key="C_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            Body=file_object,
        )
        with (
            mock.patch(
                "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
                return_value=AdapterHierarchy.from_file(
                    "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
                return_value=AdapterHierarchy.from_file(
                    "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
                ),
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.service.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.load_blob.get_s3_client",
                return_value=client_mock,
            ),
            mock.patch(
                "hetdesrun.adapters.blob_storage.write_blob.get_s3_client",
                return_value=client_mock,
            ),
        ):
            async with async_test_client_with_blob_storage_adapter as client:
                with open(
                    os.path.join(
                        "tests",
                        "data",
                        "store_object_with_class_wf_execution_input.json",
                    ),
                    encoding="utf8",
                ) as f:
                    loaded_store_object_workflow_exe_input = json.load(f)

                loaded_store_object_workflow_exe_input["workflow_wiring"]["output_wirings"] = [
                    {
                        "adapter_id": "blob-storage-adapter",
                        "ref_id": "i-i/C",
                        "ref_id_type": "THINGNODE",
                        "ref_key": (
                            "C - 2022-01-02 14:23:18+00:00 - "
                            "4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)"
                        ),
                        "type": "metadata(any)",
                        "workflow_output_name": "class_entity",
                    }
                ]
                (
                    store_response_status_code,
                    store_response_json,
                ) = await run_workflow_with_client(loaded_store_object_workflow_exe_input, client)

                assert store_response_status_code == 200
                assert store_response_json["result"] == "failure"
                assert "already contains an object" in store_response_json["error"]["message"]
                assert (
                    "write request will not be executed" in store_response_json["error"]["message"]
                )
