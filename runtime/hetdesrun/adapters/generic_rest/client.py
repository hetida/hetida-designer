"""Cached http clients for each registered generic REST adapter

One per registered generic rest adapter
"""

import logging
import threading

import httpx
import niquests
from niquests.packages.urllib3.contrib.hface.protocols.http1 import HTTP1ProtocolHyperImpl

from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)

# One cached client per adapter_key (see module docstring: one event loop per process).
_generic_rest_adapter_clients: dict[str, httpx.AsyncClient] = {}
_generic_rest_adapter_clients_lock = threading.Lock()


def _create_generic_rest_adapter_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        verify=get_config().hd_adapters_verify_certs,
        timeout=get_config().external_request_timeout,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )


def get_generic_rest_adapter_client(adapter_key: str) -> httpx.AsyncClient:
    """Return a cached httpx AsyncClient for the given generic REST adapter.

    The client is created lazily on first use and reused on subsequent calls so that its connection
    pool is shared. There is exactly one client per ``adapter_key``. Safe to call concurrently from
    multiple tasks on the (single) event loop.
    """
    # Fast path: return the cached client without acquiring the lock.
    client = _generic_rest_adapter_clients.get(adapter_key)
    if client is not None and not client.is_closed:
        return client

    with _generic_rest_adapter_clients_lock:
        # Re-check inside the lock in case another task created the client meanwhile.
        client = _generic_rest_adapter_clients.get(adapter_key)
        if client is None or client.is_closed:
            client = _create_generic_rest_adapter_client()
            _generic_rest_adapter_clients[adapter_key] = client
        return client


async def close_generic_rest_adapter_clients() -> None:
    """Close and drop all cached generic REST adapter clients.

    Intended to be called from the FastAPI application shutdown (``lifespan``).
    """
    with _generic_rest_adapter_clients_lock:
        clients = list(_generic_rest_adapter_clients.values())
        _generic_rest_adapter_clients.clear()

    for client in clients:
        try:
            await client.aclose()
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to close a cached generic REST adapter http client during shutdown",
                exc_info=True,
            )


# Cached *synchronous* niquests sessions, one per registered generic REST adapter.
#
# The framelike load path (timeseries / dataframe / multitsframe GET) streams the response body
# straight into pyarrow's JSON reader, which needs a synchronous, readable file-like (``resp.raw``).
# We therefore keep a blocking niquests.Session per adapter here (instead of the async httpx client
# above). niquests is generally faster than requests for this.
#
# The sessions are restricted to HTTP/1.1 (no HTTP/2 via TLS ALPN, no HTTP/3 via Alt-Svc), so that
# every adapter request - http or https - takes the same code path, on which the response header
# size limit is raised (see below). Framelike loads are few large streamed responses, which do not
# profit from HTTP/2 multiplexing: measured over TLS, HTTP/1.1 was even slightly faster than HTTP/2.
_generic_rest_adapter_sync_sessions: dict[str, niquests.Session] = {}
_generic_rest_adapter_sync_sessions_lock = threading.Lock()

_h11_limit_patched = False


def _raise_niquests_h11_response_header_limit() -> None:
    """Raise the HTTP/1.1 response head size limit of niquests (urllib3-future).

    urllib3-future parses HTTP/1.1 with h11, constructed with h11's default limit of 16 KiB for
    the status line plus headers, and offers no way to configure it. Generic REST adapters may send
    larger headers (e.g. a base64-encoded Data-Attributes header), which then fails with
    "Receive buffer too long". The previously used requests / http.client allowed 64 KiB per header
    line and httpx (httpcore) allows 100 KiB.

    We therefore raise the limit on each h11 connection created by urllib3-future. This only
    affects urllib3-future: h11 connections of uvicorn and httpx keep their own limits.
    """
    global _h11_limit_patched  # noqa: PLW0603
    if _h11_limit_patched:
        return

    original_init = HTTP1ProtocolHyperImpl.__init__

    def patched_init(self: HTTP1ProtocolHyperImpl) -> None:
        original_init(self)
        self._connection._max_incomplete_event_size = (
            get_config().generic_rest_adapter_max_response_header_size
        )

    HTTP1ProtocolHyperImpl.__init__ = patched_init  # type: ignore[method-assign]
    _h11_limit_patched = True


def get_generic_rest_adapter_sync_session(adapter_key: str) -> niquests.Session:
    """Return a cached synchronous niquests session for the given generic REST adapter.

    Created lazily on first use and reused afterwards so the connection pool (keep-alive) is
    shared. There is one session per ``adapter_key``.
    """
    session = _generic_rest_adapter_sync_sessions.get(adapter_key)
    if session is not None:
        return session

    with _generic_rest_adapter_sync_sessions_lock:
        session = _generic_rest_adapter_sync_sessions.get(adapter_key)
        if session is None:
            _raise_niquests_h11_response_header_limit()
            session = niquests.Session(disable_http2=True, disable_http3=True)
            _generic_rest_adapter_sync_sessions[adapter_key] = session
        return session


def close_generic_rest_adapter_sync_sessions() -> None:
    """Close and drop all cached synchronous generic REST adapter sessions.

    Intended to be called from the FastAPI application shutdown (``lifespan``).
    """
    with _generic_rest_adapter_sync_sessions_lock:
        sessions = list(_generic_rest_adapter_sync_sessions.values())
        _generic_rest_adapter_sync_sessions.clear()

    for session in sessions:
        try:
            session.close()
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to close a cached generic REST adapter sync session during shutdown",
                exc_info=True,
            )
