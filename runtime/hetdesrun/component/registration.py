"""Component entrypoint registration utilities"""

import asyncio
import functools
from collections.abc import Callable

from hetdesrun.component.load import ComponentCodeImportError
from hetdesrun.datatypes import DataType


class ComponentEntryPointRegistrationError(ComponentCodeImportError):
    pass


def register(
    *,
    inputs: dict[str, DataType],
    outputs: dict[str, DataType],
    name: str | None = None,
    description: str | None = None,
    category: str | None = None,
    id: str | None = None,  # noqa: A002
    revision_group_id: str | None = None,
    version_tag: str | None = None,
    state: str | None = None,
    released_timestamp: str | None = None,
    disabled_timestamp: str | None = None,
    is_pure_plot_component: bool | None = None,  # noqa: ARG001
) -> Callable[[Callable], Callable]:
    """Additonal features for component entrypoint functions

    This decorator can be used to provide additional features for component entrypoint
    functions which may depend on datatype infos on the inputs and outputs.

    is_pure_plot_component: This is deprecated and only exists for backwards compatibility,
    but it is ignored.
    """

    def wrapper_func(func: Callable) -> Callable:
        if not asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            def return_func_or_coro(*args, **kwargs):  # type: ignore
                return func(*args, **kwargs)

        else:

            @functools.wraps(func)
            async def return_func_or_coro(*args, **kwargs):  # type: ignore
                return await func(*args, **kwargs)

        # add input output infos to function attributes
        return_func_or_coro.inputs = inputs  # type: ignore
        return_func_or_coro.outputs = outputs  # type: ignore
        return_func_or_coro.registered_metadata = {  # type: ignore
            "inputs": inputs,
            "outputs": outputs,
            "name": name,
            "description": description,
            "category": category,
            "version_tag": version_tag,
            "id": id,
            "revision_group_id": revision_group_id,
            "state": state,
            "released_timestamp": released_timestamp,
            "disabled_timestamp": disabled_timestamp,
        }

        return return_func_or_coro

    return wrapper_func
