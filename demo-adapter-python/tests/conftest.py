import pytest
from httpx2 import ASGITransport, AsyncClient

from demo_adapter_python.webservice import app


@pytest.fixture
def async_test_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore
        base_url="http://test",
        timeout=15,
    )
