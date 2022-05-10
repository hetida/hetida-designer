"""Execution helpers"""
import asyncio
from typing import Callable, Any, Dict


def gen_default_return_for_plot_func(outputs: dict) -> dict:
    """Generate answer for plot component if it should not be executed

    If plot component is not executed, its PlotlyJson outputs should be empty dicts.
    This function prepares this output from the provided outputs
    """
    return {key: {} for key in outputs.keys()}


async def run_func_or_coroutine(
    func_or_coro: Callable[..., Any], kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """Check if input is coroutine and depending on result either await it or call as function"""
    if asyncio.iscoroutinefunction(func_or_coro):
        return await func_or_coro(**kwargs)  # type: ignore
    return func_or_coro(**kwargs)  # type: ignore
