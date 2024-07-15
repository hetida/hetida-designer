import pickle
from typing import Any


def load_pickle(path: str, **kwargs: Any) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f, **kwargs)  # noqa: S301


def write_pickle(pickle_serializable_object: Any, path: str, **kwargs: Any) -> None:
    with open(path, "wb") as f:
        pickle.dump(pickle_serializable_object, f, protocol=pickle.HIGHEST_PROTOCOL, **kwargs)
