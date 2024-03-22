from unittest import mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.kafka.config import KafkaConfig
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
            ),
        },
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        return init_app()


@pytest.fixture
def async_test_client_with_kafka_adapter(
    two_kafka_configs,
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(app=app_without_auth, base_url="http://test")
