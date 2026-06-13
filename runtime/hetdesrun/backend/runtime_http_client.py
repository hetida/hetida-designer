from contextvars import ContextVar

import httpx
from fastapi import Request

runtime_http_client: ContextVar[httpx.AsyncClient] = ContextVar("http_client")


def get_runtime_http_client() -> httpx.AsyncClient:
    """Access context var to get runtime async httpx client"""
    client = runtime_http_client.get(None)
    if client is None:
        raise RuntimeError("runtime_http_client context var content not set!")
    return client


async def get_runtime_http_client_from_request(request: Request) -> httpx.AsyncClient:
    """Get runtime async httpx client from the request object
    Usage in endpoint functions:
        async def my_endpoint(
            ...,
            runtime_http_client: httpx.AsyncClient = Depends(get_runtime_http_client_from_request)
        ):
            ...
    """
    return request.app.state.runtime_http_client  # type: ignore


async def inject_runtime_http_client(request: Request) -> None:
    """FastAPI dependency injecting runtime http client into contextvar

    Use as a dependency to relevant endpoints:

        @app.get("/my_endpoint", dependencies=[Depends(inject_runtime_http_client)])
        async def my_endpoint():
            ...

    In these endpoints: access via the function get_runtime_http_client above!
    """
    runtime_http_client.set(await get_runtime_http_client_from_request(request))
