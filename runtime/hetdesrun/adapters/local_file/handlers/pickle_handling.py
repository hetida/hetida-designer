import pickle  # nosec: B403
from typing import Any

# Security note (reviewed, accepted by design): unpickling executes embedded code,
# this is inheritent to Python unpickling. The local-file adapter's configured
# directory and everything reahable from there is TRUSTED as well as the
# execution context / users under which this unpickling happens.


def load_pickle(path: str, **kwargs: Any) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f, **kwargs)  # noqa: S301 # nosec: B301


def write_pickle(pickle_serializable_object: Any, path: str, **kwargs: Any) -> None:
    with open(path, "wb") as f:
        pickle.dump(pickle_serializable_object, f, protocol=pickle.HIGHEST_PROTOCOL, **kwargs)
