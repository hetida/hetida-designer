"""Execution helpers"""
import asyncio
from collections.abc import Callable
from typing import Any


async def run_func_or_coroutine(
    func_or_coro: Callable[..., Any], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Check if input is coroutine and depending on result either await it or call as function"""
    if asyncio.iscoroutinefunction(func_or_coro):
        return await func_or_coro(**kwargs)  # type: ignore
    return func_or_coro(**kwargs)  # type: ignore
