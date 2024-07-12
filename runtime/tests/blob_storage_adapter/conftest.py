from collections.abc import Generator
from unittest import mock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from hetdesrun.adapters.blob_storage.models import (
    AdapterHierarchy,
    BlobStorageStructureSource,
    IdString,
)
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="session")
def mock_adapter_hierarchy_location_in_config() -> Generator:
    with mock.patch(
        "hetdesrun.adapters.blob_storage.config.get_blob_adapter_config",
        adapter_hierarchy_location="tests/data/blob_storage/blob_storage_adapter_hierarchy.json",
    ) as _fixture:
        yield _fixture


@pytest.fixture
def async_test_client_with_blob_storage_adapter(
    app_without_auth_with_blob_storage_adapter: FastAPI,
) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app_without_auth_with_blob_storage_adapter),
        base_url="http://test",
    )


@pytest.fixture(scope="session")
def mocked_blob_storage_sources():
    return [
        BlobStorageStructureSource(
            id="i-i/A_2022-01-02T14:23:18+00:00_4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f.pkl",
            thingNodeId="i-i/A",
            name="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",
            path="i-i/A",
            metadataKey="A - 2022-01-02 14:23:18+00:00 - 4ec1c6fd-03cc-4c21-8a74-23f3dd841a1f (pkl)",  # noqa: E501
        ),
        BlobStorageStructureSource(
            id="i-i/A_2022-01-02T14:57:31+00:00_0788f303-61ce-47a9-b5f9-ec7b0de3be43.pkl",
            thingNodeId="i-i/A",
            name="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)",
            path="i-i/A",
            metadataKey="A - 2022-01-02 14:57:31+00:00 - 0788f303-61ce-47a9-b5f9-ec7b0de3be43 (pkl)",  # noqa: E501
        ),
        BlobStorageStructureSource(
            id="i-i/B_2022-01-02T14:25:56+00:00_f1a16db0-c075-4ed9-8953-f97c2dc3ae51.pkl",
            thingNodeId="i-i/B",
            name="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51 (pkl)",
            path="i-i/B",
            metadataKey="B - 2022-01-02 14:25:56+00:00 - f1a16db0-c075-4ed9-8953-f97c2dc3ae51 (pkl)",  # noqa: E501
        ),
        BlobStorageStructureSource(
            id="i-i/D_2022-03-08T17:23:18+00:00_94726ca0-9b4d-4b72-97be-d3ef085e16fa.pkl",
            thingNodeId="i-i/D",
            name="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",
            path="i-i/D",
            metadataKey="D - 2022-03-08 17:23:18+00:00 - 94726ca0-9b4d-4b72-97be-d3ef085e16fa (pkl)",  # noqa: E501
        ),
        BlobStorageStructureSource(
            id="i-i/D_2022-04-02T13:28:29+00:00_af77087b-a064-4ff9-9c4a-d23b2c503ade.pkl",
            thingNodeId="i-i/D",
            name="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade (pkl)",
            path="i-i/D",
            metadataKey="D - 2022-04-02 13:28:29+00:00 - af77087b-a064-4ff9-9c4a-d23b2c503ade (pkl)",  # noqa: E501
        ),
        BlobStorageStructureSource(
            id="i-ii/E_2022-01-02T14:23:18+00:00_3bd049f4-1d0e-4993-ac4c-306ebe320144.pkl",
            thingNodeId="i-ii/E",
            name="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144 (pkl)",
            path="i-ii/E",
            metadataKey="E - 2022-01-02 14:23:18+00:00 - 3bd049f4-1d0e-4993-ac4c-306ebe320144 (pkl)",  # noqa: E501
        ),
    ]


@pytest.fixture(scope="session")
def mocked_blob_storage_sources_dict(mocked_blob_storage_sources):
    return {src.id: src for src in mocked_blob_storage_sources}


@pytest.fixture(scope="session")
def mocked_blob_storage_source_by_thing_node_id_dict(mocked_blob_storage_sources):
    source_by_thing_node_id_dict: dict[IdString, list[BlobStorageStructureSource]] = {}
    for src in mocked_blob_storage_sources:
        if src.thingNodeId not in source_by_thing_node_id_dict:
            source_by_thing_node_id_dict[src.thingNodeId] = [src]
        else:
            source_by_thing_node_id_dict[src.thingNodeId].append(src)
    return source_by_thing_node_id_dict


@pytest.fixture(scope="function")  # noqa: PT003
def _mocked_source_and_structure(
    mocked_blob_storage_sources,
    mocked_blob_storage_sources_dict,
    mocked_blob_storage_source_by_thing_node_id_dict,
):
    async def mocked_get_source_by_parent_id(
        parent_id: IdString,
    ) -> list[BlobStorageStructureSource]:
        if parent_id not in mocked_blob_storage_source_by_thing_node_id_dict:
            return []
        return mocked_blob_storage_source_by_thing_node_id_dict[parent_id]

    async def mocked_get_source_by_id(
        id: IdString,  # noqa: A002
    ) -> BlobStorageStructureSource:
        return mocked_blob_storage_sources_dict[id]

    with (
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_adapter_structure",
            return_value=AdapterHierarchy.from_file(
                "tests/data/blob_storage/blob_storage_adapter_hierarchy.json"
            ),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_all_sources",
            return_value=mocked_blob_storage_sources,
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_source_by_id",
            new=mocked_get_source_by_id,
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.structure.get_sources_by_parent_id",
            new=mocked_get_source_by_parent_id,
        ) as _fixture,
    ):
        yield


@pytest.fixture(scope="session")
def app_without_auth_with_blob_storage_adapter(
    mock_adapter_hierarchy_location_in_config,
) -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture(scope="function")  # noqa: PT003
def app_without_auth_with_blob_storage_adapter_with_mocked_structure(
    _mocked_source_and_structure,
    mock_adapter_hierarchy_location_in_config,
) -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture(scope="function")  # noqa: PT003
def async_test_client_with_blob_storage_adapter_with_mocked_structure(
    app_without_auth_with_blob_storage_adapter_with_mocked_structure: FastAPI,
) -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(
            app=app_without_auth_with_blob_storage_adapter_with_mocked_structure
        ),
        base_url="http://test",
    )
