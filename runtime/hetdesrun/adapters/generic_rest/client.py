"""Cached http clients for each registered generic REST adapter

One per registered generic rest adapter
"""

import logging
import threading

import httpx
import niquests

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
# above). niquests (HTTP/2+3 capable) is generally faster than requests for this
_generic_rest_adapter_sync_sessions: dict[str, niquests.Session] = {}
_generic_rest_adapter_sync_sessions_lock = threading.Lock()


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
            session = niquests.Session()
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
