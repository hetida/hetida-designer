"""Basic Python Object serialization / model repository

This is a very basic / demo implementation of a model repository and allows
to persist Python objects from a component and load them in another one -
possibly during execution of another workflow. A typical use case is training a
model in a training workflow and persisting it, then load it for predicting in
a prediction workflow.

WARNING: This is currently a proof of concept / work in progress.
For example object names and tags should be validated before actually trying
to write to the file system. It may be replaced by a proper model/object repo
framework in the future. In production deployments models should be stored and
loaded through appropriate adapters (see hetida designer adapter system)
and not via components.
"""

import os
from typing import Any

import joblib

from hetdesrun.webservice.config import get_config


def get_object_path(name: str, tag: str) -> str:
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
