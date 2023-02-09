from unittest import mock

import pytest

from hetdesrun.persistence import sessionmaker


@pytest.mark.asyncio
async def test_get_all_adapters(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get("/api/adapters/")

        assert response.status_code == 200
        assert len(response.json()) == 4
