import json
from unittest import mock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.config import KafkaConfig
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="function")  # noqa: PT003
def two_kafka_configs():
    with mock.patch(
        "hetdesrun.adapters.kafka.config.kafka_adapter_config.kafka_configs",
        new={
            "test_kafka_config1": KafkaConfig(
                display_name="Test Kafka Config No 1",
                topic="multi ts ingestion",
                types=[ExternalType("multitsframe")],
                consumable=True,
            ),
            "test_kafka_config2": KafkaConfig(
                display_name="Test Kafka Config No 2",
                topic="multi ts ingestion",
                types=None,
                consumable=True,
            ),
        },
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def _db_with_pass_through_component(mocked_clean_test_db_session):
    with open(
        "transformations/components/connectors/pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture
def async_test_client_with_kafka_adapter(
    two_kafka_configs,
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app_without_auth), base_url="http://test")


@pytest_asyncio.fixture
async def open_async_test_client_with_kafka_adapter(
    async_test_client_with_kafka_adapter,
):
    async with async_test_client_with_kafka_adapter as client:
        yield client
