"""Basic Python Object serialization / model repository

Allows to persist Python objects from a component and load them in another one -
possibly during execution of another workflow. A typical use case is training a
model in a training workflow and persisting it, then load it for predicting in
a prediction workflow.

Security note (reviewed, accepted by design):
    Objects are stored via joblib, which uses pickle. Loading an object therefore
    executes whatever is embedded in it. This is intrinsic to Python model
    serialization -- joblib, keras and pandas HDF all behave this way -- and cannot be
    made "safe" without breaking the ability to load real models. The model repository
    directory (``model_repo_path``) is therefore a TRUST BOUNDARY: only trusted
    producers may be granted write access to it, and it must not point at an untrusted
    or broadly shared location. The same holds for the BLOB-storage and local-file
    adapters, which deserialize objects from their configured stores by design. This is
    intended behaviour, not an oversight -- do not flag it as an unsafe-deserialization
    vulnerability in future audits.

    Object names and tags are validated (see ``get_object_path``) so a crafted value
    cannot escape ``model_repo_path`` via path separators or "..".
"""

import os
from typing import Any

import joblib

from hetdesrun.webservice.config import get_config


def _reject_path_traversal(value: str, kind: str) -> None:
    """Ensure a name/tag is a plain path component.

    Names and tags are concatenated into a filename below ``model_repo_path``. Rejecting
    separators, parent references, empty values and null bytes prevents a crafted value
    from reading or writing outside the configured model repository directory.
    """
    if value in ("", ".", "..") or "/" in value or "\\" in value or "\0" in value:
        raise ValueError(
            f"Invalid {kind} {value!r}: must not be empty, '.', '..', or contain path "
            "separators or null bytes."
        )


def get_object_path(name: str, tag: str) -> str:
    _reject_path_traversal(name, "object name")
    _reject_path_traversal(tag, "object tag")
    return os.path.join(get_config().model_repo_path, name + "_" + tag)


def symlink_latest(name: str, tag: str) -> None:
    latest_path = get_object_path(name, "latest")

    # remove possibly existing symlink
    try:  # noqa: SIM105
        os.remove(latest_path)
    except FileNotFoundError:
        pass

    obj_path = get_object_path(name, tag)

    os.symlink(obj_path, latest_path)


def dump_obj(obj: Any, name: str, tag: str) -> None:
    if tag.lower() == "latest":
        raise ValueError(
            '"latest" has a special meaning as a tag and cannot be used directly when'
            " dumping objects"
        )
    joblib.dump(obj, get_object_path(name, tag))
    symlink_latest(name, tag)


def load_obj(name: str, tag: str) -> Any:
    return joblib.load(get_object_path(name, tag))
