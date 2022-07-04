import pytest
from httpx import AsyncClient

from demo_adapter_python.webservice import app


@pytest.fixture
def async_test_client():
    return AsyncClient(app=app, base_url="http://test")
