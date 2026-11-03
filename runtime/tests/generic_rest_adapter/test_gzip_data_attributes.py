"""gzip-compressed Data-Attributes headers (metadata) of generic REST adapter responses"""

import base64
import gzip
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from unittest import mock

import pytest

from hetdesrun.adapters.exceptions import AdapterHandlingException
from hetdesrun.adapters.generic_rest.client import close_generic_rest_adapter_sync_sessions
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_framelike import (
    DATA_ATTRIBUTES_ACCEPT_ENCODING_HEADER,
    decode_attributes,
    load_framelike_data,
)
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource
from hetdesrun.webservice.config import get_config

METADATA: dict[str, Any] = {
    "a": {
        "dataset_metadata": {"metric_key": "id", "single_metric": "a", "queried_metrics": ["a"]},
        "metrics": [{"id": "a", "name": "A", "comments": [{"content": "maintenance"}] * 100}],
    }
}


def gzip_encoded(metadata: Any, prefix: bytes = b"") -> str:
    return base64.b64encode(gzip.compress(prefix + json.dumps(metadata).encode("utf-8"))).decode()


def base64_of(data: bytes) -> str:
    return base64.b64encode(data).decode()


def test_plain_data_attributes() -> None:
    assert decode_attributes(encode_attributes(METADATA)) == METADATA


def test_gzip_compressed_data_attributes() -> None:
    encoded = gzip_encoded(METADATA)

    assert decode_attributes(encoded) == METADATA
    assert len(encoded) < len(encode_attributes(METADATA)) / 5


def test_gzip_compressed_json_with_leading_whitespace() -> None:
    assert decode_attributes(gzip_encoded(METADATA, prefix=b"\n  ")) == METADATA


def test_decompressed_size_is_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    # a decompression bomb: uniform data compresses extremely
    encoded = base64_of(gzip.compress(b'{"x": "' + b"x" * 10_000_000 + b'"}'))
    assert len(encoded) < 20_000
    monkeypatch.setattr(get_config(), "generic_rest_adapter_max_decompressed_metadata_size", 10**6)

    with pytest.raises(ValueError, match="exceeds 1000000 bytes when decompressed"):
        decode_attributes(encoded)


def test_metadata_of_exactly_the_maximum_size(monkeypatch: pytest.MonkeyPatch) -> None:
    data = json.dumps(METADATA).encode("utf-8")
    monkeypatch.setattr(
        get_config(), "generic_rest_adapter_max_decompressed_metadata_size", len(data)
    )

    assert decode_attributes(base64_of(gzip.compress(data))) == METADATA


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (gzip.compress(json.dumps(METADATA).encode())[:-20], "truncated"),
        (b"\x1f\x8b" + b"no gzip data", "Invalid gzip data"),
        (gzip.compress(json.dumps(METADATA).encode()) + b"garbage", "followed by further data"),
    ],
)
def test_invalid_gzip_data(data: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        decode_attributes(base64_of(data))


@pytest.mark.parametrize("header", ["not base64!", base64_of(b"no json")])
def test_invalid_data_attributes(header: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        decode_attributes(header)


_BODY = b'{"timeseriesId":"a","timestamp":"2020-01-01T00:00:00.000Z","value":1.0}\n'


class _AdapterHandler(BaseHTTPRequestHandler):
    """An adapter sending its metadata gzip-compressed, also without the request header"""

    data_attributes = gzip_encoded(METADATA)
    received_headers: list[dict[str, str]] = []

    def do_GET(self) -> None:  # noqa: N802
        _AdapterHandler.received_headers.append(dict(self.headers))
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(_BODY)))
        self.send_header("Data-Attributes", self.data_attributes)
        self.end_headers()
        self.wfile.write(_BODY)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def adapter(monkeypatch: pytest.MonkeyPatch) -> Iterator[type[_AdapterHandler]]:
    # Proxy environment variables would route requests to 127.0.0.1 through the proxy
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AdapterHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    async def fake_base_url(adapter_key: str) -> str:
        return f"http://127.0.0.1:{server.server_port}"

    monkeypatch.setattr(
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        fake_base_url,
    )
    _AdapterHandler.received_headers = []
    try:
        yield _AdapterHandler
    finally:
        close_generic_rest_adapter_sync_sessions()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


async def load(adapter_key: str = "gzip_test_adapter") -> Any:
    return await load_framelike_data(
        [FilteredSource(ref_id="a", type=ExternalType.TIMESERIES_FLOAT)],
        additional_params=[],
        adapter_key=adapter_key,
        endpoint="timeseries",
    )


@pytest.mark.asyncio
async def test_loading_with_gzip_compressed_data_attributes(adapter: Any) -> None:
    df = await load()

    assert len(df) == 1
    assert df.attrs == METADATA
    # the runtime announces that it understands gzip-compressed Data-Attributes
    assert adapter.received_headers[0][DATA_ATTRIBUTES_ACCEPT_ENCODING_HEADER] == "gzip"


@pytest.mark.asyncio
async def test_undecodable_data_attributes_let_loading_fail(adapter: Any) -> None:
    with (
        mock.patch.object(adapter, "data_attributes", base64_of(b"\x1f\x8bbroken")),
        pytest.raises(AdapterHandlingException, match="generic rest adapter gzip_test_adapter"),
    ):
        await load()
