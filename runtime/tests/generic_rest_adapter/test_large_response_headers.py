"""Large response headers (e.g. a big Data-Attributes header) must not break framelike loading.

niquests / urllib3-future parse HTTP/1.1 via h11, whose default limit for the response head is only
16 KiB ("Receive buffer too long"). The generic REST adapter sends DataFrame attrs base64-encoded in
the Data-Attributes response header, which can easily exceed that. These tests talk to a real local
HTTP server so the actual h11 parsing is exercised.
"""

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from hetdesrun.adapters.generic_rest.client import (
    close_generic_rest_adapter_sync_sessions,
    get_generic_rest_adapter_sync_session,
)
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.generic_rest.load_framelike import load_framelike_data
from hetdesrun.adapters.generic_rest.send_framelike import encode_attributes
from hetdesrun.models.data_selection import FilteredSource

_ATTRIBUTES = {"large": "x" * 100_000}
_BODY = (
    b'{"timeseriesId":"a","timestamp":"2020-01-01T00:00:00.000Z","value":1.0}\n'
    b'{"timeseriesId":"a","timestamp":"2020-01-01T00:01:00.000Z","value":2.0}\n'
)


class _LargeHeaderHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Content-Length", str(len(_BODY)))
        self.send_header("Data-Attributes", encode_attributes(_ATTRIBUTES))
        self.end_headers()
        self.wfile.write(_BODY)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture()
def large_header_server(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    # Local loopback server on a free port. Proxy environment variables (e.g. on CI runners behind
    # a proxy) would otherwise route the requests to 127.0.0.1 through the proxy.
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LargeHeaderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        close_generic_rest_adapter_sync_sessions()
        server.shutdown()  # stops serve_forever and waits for it to return
        server.server_close()  # closes the listening socket
        thread.join(timeout=5)


def test_sync_session_accepts_large_response_headers(large_header_server: str) -> None:
    session = get_generic_rest_adapter_sync_session("large_header_test_adapter")
    resp = session.get(large_header_server + "/timeseries")
    assert resp.status_code == 200
    assert len(resp.headers["Data-Attributes"]) > 16 * 1024


@pytest.mark.asyncio
async def test_load_framelike_data_with_large_data_attributes_header(
    large_header_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_base_url(adapter_key: str) -> str:
        return large_header_server

    monkeypatch.setattr(
        "hetdesrun.adapters.generic_rest.load_framelike.get_generic_rest_adapter_base_url",
        fake_base_url,
    )

    df = await load_framelike_data(
        [FilteredSource(ref_id="a", type=ExternalType.TIMESERIES_FLOAT)],
        additional_params=[],
        adapter_key="large_header_test_adapter",
        endpoint="timeseries",
    )
    assert len(df) == 2
    assert df.attrs == _ATTRIBUTES


def test_sync_session_is_restricted_to_http_1_1(large_header_server: str) -> None:
    # HTTP/2 and HTTP/3 are disabled, so that the raised header size limit also applies to https
    session = get_generic_rest_adapter_sync_session("large_header_test_adapter")
    assert session._disable_http2
    assert session._disable_http3
    resp = session.get(large_header_server + "/timeseries")
    assert resp.http_version == 11
