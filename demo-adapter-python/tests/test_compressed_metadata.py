"""gzip-compressed Data-Attributes of the GET endpoints, if the runtime announces it"""

import base64
import gzip
import json

import pytest
from httpx2 import AsyncClient

from demo_adapter_python.config import demo_adapter_config

INTERVAL = {"from": "2020-01-01T00:00:00Z", "to": "2020-01-01T03:00:00Z"}
REQUESTS = [
    ("/timeseries", {"id": "root.plantA.picklingUnit.influx.temp"} | INTERVAL),
    ("/multitsframe", {"id": "root.plantA.temperatures"} | INTERVAL),
    ("/singletsframe", {"id": "root.plantA.picklingUnit.influx.temp_with_state"} | INTERVAL),
    ("/dataframe", {"id": "root.plantA.maintenance_events"}),
]
ANNOUNCEMENT = {"Data-Attributes-Accept-Encoding": "gzip"}


def decoded(header: str) -> tuple[bool, dict]:
    """Whether the header is gzip-compressed and the metadata it contains"""
    data = base64.b64decode(header)
    compressed = data[:2] == b"\x1f\x8b"
    return compressed, json.loads(gzip.decompress(data) if compressed else data)


@pytest.mark.asyncio
@pytest.mark.parametrize(("path", "params"), REQUESTS)
async def test_compressed_if_announced(
    async_test_client: AsyncClient, path: str, params: dict
) -> None:
    async with async_test_client as client:
        plain = (await client.get(path, params=params)).headers["Data-Attributes"]
        compressed = (await client.get(path, params=params, headers=ANNOUNCEMENT)).headers[
            "Data-Attributes"
        ]

    plain_is_compressed, plain_metadata = decoded(plain)
    is_compressed, metadata = decoded(compressed)
    assert not plain_is_compressed
    assert is_compressed
    # the same metadata, apart from e.g. timestamps of the request
    assert metadata.keys() == plain_metadata.keys()


@pytest.mark.asyncio
async def test_timeseries_metadata_is_the_same_compressed(async_test_client: AsyncClient) -> None:
    path, params = REQUESTS[0]
    async with async_test_client as client:
        plain = (await client.get(path, params=params)).headers["Data-Attributes"]
        compressed = (await client.get(path, params=params, headers=ANNOUNCEMENT)).headers[
            "Data-Attributes"
        ]

    assert decoded(compressed)[1] == decoded(plain)[1]
    assert len(compressed) < len(plain)


@pytest.mark.asyncio
@pytest.mark.parametrize("announcement", ["deflate", "br, gzip ", "identity"])
async def test_compressed_only_if_gzip_is_announced(
    async_test_client: AsyncClient, announcement: str
) -> None:
    path, params = REQUESTS[0]
    async with async_test_client as client:
        header = (
            await client.get(
                path, params=params, headers={"Data-Attributes-Accept-Encoding": announcement}
            )
        ).headers["Data-Attributes"]

    assert decoded(header)[0] == ("gzip" in announcement)


@pytest.mark.asyncio
async def test_compression_can_be_switched_off(
    async_test_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(demo_adapter_config, "compress_metadata", False)
    path, params = REQUESTS[0]
    async with async_test_client as client:
        header = (await client.get(path, params=params, headers=ANNOUNCEMENT)).headers[
            "Data-Attributes"
        ]

    assert not decoded(header)[0]
