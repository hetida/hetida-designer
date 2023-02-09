from keyword import iskeyword
from typing import Any, Protocol, TypeVar, Union


class NamedEntity(Protocol):
    name: str


class OptionallyNamedEntity(Protocol):
    name: str | None


def valid_python_identifier(cls: Any, name: str) -> str:  # noqa: ARG001
    if name.isidentifier() and not iskeyword(name):
        return name
    raise ValueError(f"{name} is not a valid Python identifier")


T = TypeVar("T", bound=Union[NamedEntity, OptionallyNamedEntity])


def names_unique(cls: Any, inputs_or_outputs: list[T]) -> list[T]:  # noqa: ARG001
    if any(io.name is None for io in inputs_or_outputs):
        raise ValueError("uniqueness of names can only be checked if name is not None")
    if len({io.name for io in inputs_or_outputs}) == len(inputs_or_outputs):
        return inputs_or_outputs
    raise ValueError("duplicates in names not allowed.")
