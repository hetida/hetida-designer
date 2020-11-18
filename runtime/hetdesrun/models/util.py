from keyword import iskeyword

from typing import Protocol, List, TypeVar, Any


class NamedEntity(Protocol):
    name: str


def valid_python_identifier(
    cls: Any, name: str  # pylint: disable=unused-argument
) -> str:
    if name.isidentifier() and not iskeyword(name):
        return name
    raise ValueError(f"{name} is not a valid Python identifier")


T = TypeVar("T", bound=NamedEntity)


def names_unique(
    cls: Any, inputs_or_outputs: List[T]  # pylint: disable=unused-argument
) -> List[T]:
    if len(set(i.name for i in inputs_or_outputs)) == len(inputs_or_outputs):
        return inputs_or_outputs
    raise ValueError("duplicates in names not allowed.")
