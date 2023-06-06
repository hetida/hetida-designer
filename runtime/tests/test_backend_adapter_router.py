from unittest import mock

import pytest
from httpx import AsyncClient
from sqlalchemy.future.engine import Engine

from hetdesrun.persistence import sessionmaker


@pytest.mark.asyncio
async def test_get_all_default_adapters(
    async_test_client: AsyncClient, clean_test_db_engine: Engine
) -> None:
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get("/api/adapters/")

        assert response.status_code == 200
        adapter_list = response.json()
        assert len(adapter_list) == 4
