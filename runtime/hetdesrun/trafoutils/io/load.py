"""Utilities for loading ensembles of transformation revisions from disk"""

import importlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import parse_file_as

from hetdesrun.component.load import (
    ComponentCodeImportError,
    import_func_from_code,
    module_path_from_code,
)
from hetdesrun.exportimport.export import save_transformation
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IO, IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import Type, get_uuid_from_seed

logger = logging.getLogger(__name__)


def load_json(path: str) -> Any:
    """Load arbitrary json, defaulting to None if file is not found"""
    try:
        with open(path, encoding="utf8") as f:
            loaded_json_object = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find json file at path %s", path)
        loaded_json_object = None
    return loaded_json_object


def load_python_file(path: str) -> Optional[str]:
    """Load pyython code from a file

    Returns None if file is not found, the contained code as str otherwise.
    """
    try:
        with open(path, "r", encoding="utf8") as f:
            python_code = f.read()
    except FileNotFoundError:
        logger.error("Could not find python file at path %s", path)
        python_code = None
    return python_code


def transformation_revision_from_python_code(code: str) -> Any:
    """Get the TransformationRevision as a json-like object from just the Python code

    This uses information from the register decorator or a global variable COMPONENT_INFO
    and docstrings.

    Note: This needs to import the provided code, which may have arbitrary side effects
    and security implications.
    """

    try:
        main_func = import_func_from_code(code, "main")
    except ComponentCodeImportError as e:
        logging.debug(
            "Could not load main function due to error during import of component code:\n%s",
            str(e),
        )
        raise e

    module_path = module_path_from_code(code)
    mod = importlib.import_module(module_path)

    mod_docstring = mod.__doc__ or ""
    mod_docstring_lines = mod_docstring.splitlines()

    if hasattr(main_func, "registered_metadata"):
        logger.info("Get component info from registered metadata")
        component_name = main_func.registered_metadata["name"] or (  # type: ignore
            "Unnamed Component"
        )

        component_description = main_func.registered_metadata["description"] or (  # type: ignore
            "No description provided"
        )

        component_category = main_func.registered_metadata["category"] or (  # type: ignore
            "Other"
        )

        component_id = main_func.registered_metadata["id"] or (uuid4())  # type: ignore

        component_group_id = main_func.registered_metadata["revision_group_id"] or (  # type: ignore
            uuid4()
        )

        component_tag = main_func.registered_metadata["version_tag"] or ("1.0.0")  # type: ignore

        component_inputs = main_func.registered_metadata["inputs"]  # type: ignore

        component_outputs = main_func.registered_metadata["outputs"]  # type: ignore

        component_state = main_func.registered_metadata["state"] or "RELEASED"  # type: ignore

        component_released_timestamp = main_func.registered_metadata[  # type: ignore
            "released_timestamp"
        ] or (
            datetime.now(timezone.utc).isoformat()
            if component_state == "RELEASED"
            else None
        )

        component_disabled_timestamp = main_func.registered_metadata[  # type: ignore
            "disabled_timestamp"
        ] or (
            datetime.now(timezone.utc).isoformat()
            if component_state == "DISABLED"
            else None
        )

    elif hasattr(mod, "COMPONENT_INFO"):
        logger.info("Get component info from dictionary in code")
        info_dict = mod.COMPONENT_INFO
        component_inputs = info_dict.get("inputs", {})
        component_outputs = info_dict.get("outputs", {})
        component_name = info_dict.get("name", "Unnamed Component")
        component_description = info_dict.get("description", "No description provided")
        component_category = info_dict.get("category", "Other")
        component_tag = info_dict.get("version_tag", "1.0.0")
        component_id = info_dict.get("id", uuid4())
        component_group_id = info_dict.get("revision_group_id", uuid4())
        component_state = info_dict.get("state", "RELEASED")
        component_released_timestamp = info_dict.get(
            "released_timestamp",
            datetime.now(timezone.utc).isoformat()
            if component_state == "RELEASED"
            else None,
        )
        component_disabled_timestamp = info_dict.get(
            "released_timestamp",
            datetime.now(timezone.utc).isoformat()
            if component_state == "DISABLED"
            else None,
        )
    else:
        raise ComponentCodeImportError

    component_documentation = "\n".join(mod_docstring_lines[2:])

    transformation_revision = TransformationRevision(
        id=component_id,
        revision_group_id=component_group_id,
        name=component_name,
        description=component_description,
        category=component_category,
        version_tag=component_tag,
        type=Type.COMPONENT,
        state=component_state,
        released_timestamp=component_released_timestamp,
        disabled_timestamp=component_disabled_timestamp,
        documentation=component_documentation,
        io_interface=IOInterface(
            inputs=[
                IO(
                    id=get_uuid_from_seed("component_input_" + input_name),
                    name=input_name,
                    data_type=input_data_type,
                )
                for input_name, input_data_type in component_inputs.items()
            ],
            outputs=[
                IO(
                    id=get_uuid_from_seed("component_output_" + output_name),
                    name=output_name,
                    data_type=output_data_type,
                )
                for output_name, output_data_type in component_outputs.items()
            ],
        ),
        content=code,
        test_wiring=WorkflowWiring(),
    )

    tr_json = json.loads(transformation_revision.json())

    return tr_json


def load_transformation_revisions_from_directory(
    download_path: str, transform_py_to_json: bool = False
) -> Tuple[Dict[UUID, TransformationRevision], Dict[UUID, str]]:
    transformation_dict: Dict[UUID, TransformationRevision] = {}
    path_dict: Dict[UUID, str] = {}

    for root, _, files in os.walk(download_path):
        for file in files:
            path = os.path.join(root, file)
            ext = os.path.splitext(path)[1]
            if ext not in (".py", ".json"):
                logger.warning(
                    "Invalid file extension '%s' to load transformation revision from: %s",
                    ext,
                    path,
                )
                continue
            if ext == ".py":
                logger.info("Loading transformation from python file %s", path)
                python_code = load_python_file(path)
                if python_code is not None:
                    try:
                        transformation_json = transformation_revision_from_python_code(
                            python_code
                        )
                    except ComponentCodeImportError as e:
                        logging.error(
                            "Could not load main function from %s\n"
                            "due to error during import of component code:\n%s",
                            path,
                            str(e),
                        )

            if ext == ".json":
                logger.info("Loading transformation from json file %s", path)
                transformation_json = load_json(path)
            try:
                transformation = TransformationRevision(**transformation_json)
            except ValueError as err:
                logger.error(
                    "ValueError for json from path %s:\n%s", download_path, str(err)
                )
            else:
                transformation_dict[transformation.id] = transformation
                if ext == ".py":
                    if transform_py_to_json:
                        path = save_transformation(
                            tr=transformation, download_path=download_path
                        )
                        path_dict[transformation.id] = path
                else:
                    path_dict[transformation.id] = path

    return transformation_dict, path_dict


def load_trafos_from_trafo_list_json_file(
    path: str,
) -> List[TransformationRevision]:
    """Load trafo rev list from a json file

    For example the json of api/transformations GET endpoint response written into
    a file is a valid input for this function.
    """

    trafo_revisions = parse_file_as(List[TransformationRevision], path)
    return trafo_revisions
