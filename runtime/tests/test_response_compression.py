"""Response-compression (GZipMiddleware) configuration.

Compression is off by default: gzip is synchronous in the event loop and costs on the order of
100ms on multi-MB responses (large plotly plots) - a net latency loss on fast links and a block on
concurrency. These tests pin the toggle and that the compression middleware wraps responses when it
is enabled. (The internal backend->runtime hop requesting no compression is covered in
test_backend_transformation_router.test_execute_for_separate_runtime_container.)
"""

from unittest import mock

from fastapi.middleware.gzip import GZipMiddleware

from hetdesrun.webservice.application import get_middleware
from hetdesrun.webservice.config import get_config


def _gzip_middlewares(middlewares: list) -> list:
    return [m for m in middlewares if m.cls is GZipMiddleware]


def test_compression_is_off_by_default() -> None:
    assert get_config().response_compression_enabled is False
    assert _gzip_middlewares(get_middleware()) == []


def test_compression_can_be_enabled_with_configured_level() -> None:
    with (
        mock.patch.object(get_config(), "response_compression_enabled", True),
        mock.patch.object(get_config(), "response_compression_level", 3),
    ):
        middlewares = get_middleware()
        gzip_middlewares = _gzip_middlewares(middlewares)

        assert len(gzip_middlewares) == 1
        assert gzip_middlewares[0].kwargs["compresslevel"] == 3
        # Stays outermost so it wraps the (already serialized) response body.
        assert middlewares[0].cls is GZipMiddleware
