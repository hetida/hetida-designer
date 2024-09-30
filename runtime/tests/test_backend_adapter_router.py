import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_all_default_adapters(
    async_test_client: AsyncClient, mocked_clean_test_db_session
) -> None:
    async with async_test_client as ac:
        response = await ac.get("/api/adapters/")

    assert response.status_code == 200
    adapter_list = response.json()
    assert len(adapter_list) == 6
