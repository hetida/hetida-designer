import os
import json
import logging
import importlib

from uuid import UUID
from posixpath import join as posix_urljoin
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests

from hetdesrun.utils import (
    Type,
    State,
    get_uuid_from_seed,
    get_auth_headers,
    get_backend_basic_auth,
    selection_list_empty_or_contains_value,
    criterion_unset_or_matches_value,
)

from hetdesrun.component.load import (
    import_func_from_code,
    module_path_from_code,
)

from hetdesrun.component.code import update_code

from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.persistence.models.io import (
    IOInterface,
    IO,
)

from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.models.code import ComponentInfo

from hetdesrun.webservice.config import runtime_config

logger = logging.getLogger(__name__)


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            workflow_json = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find json file at path %s", path)
        workflow_json = None
    return workflow_json


def load_python_file(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            python_file = f.read()
    except FileNotFoundError:
        logger.error("Could not find python file at path %s", path)
        python_file = None
    return python_file


def transformation_revision_from_python_code(code: str) -> Any:
    """Get the TransformationRevision as a json file from just the Python code of some component
    This uses information from the register decorator and docstrings.
    Note: This needs to import the code module, which may have arbitrary side effects and security
    implications.
    """

    main_func = import_func_from_code(code, "main")

    module_path = module_path_from_code(code)
    mod = importlib.import_module(module_path)

    mod_docstring = mod.__doc__ or ""
    mod_docstring_lines = mod_docstring.splitlines()

    component_name = main_func.registered_metadata["name"] or (  # type: ignore
        "Unnamed Component"
    )

    component_description = main_func.registered_metadata["description"] or (  # type: ignore
        "No description provided"
    )

    component_category = main_func.registered_metadata["category"] or (  # type: ignore
        "Other"
    )

    component_id = main_func.registered_metadata["id"] or (  # type: ignore
        get_uuid_from_seed(str(component_name))
    )

    component_group_id = main_func.registered_metadata["revision_group_id"] or (  # type: ignore
        get_uuid_from_seed(str(component_name))
    )

    component_tag = main_func.registered_metadata["version_tag"] or ("1.0.0")  # type: ignore

    component_code = update_code(
        existing_code=code,
        component_info=ComponentInfo(
            input_types_by_name=main_func.registered_metadata["inputs"],  # type: ignore
            output_types_by_name=main_func.registered_metadata["outputs"],  # type: ignore
            name=component_name,
            description=component_description,
            category=component_category,
            id=component_id,
            revision_group_id=component_group_id,
            version_tag=component_tag,
        ),
    )

    component_documentation = "\n".join(mod_docstring_lines[2:])

    transformation_revision = TransformationRevision(
        id=component_id,
        revision_group_id=component_group_id,
        name=component_name,
        description=component_description,
        category=component_category,
        version_tag=component_tag,
        released_timestamp=datetime.now(),
        disabled_timestamp=None,
        state=State.RELEASED,
        type=Type.COMPONENT,
        documentation=component_documentation,
        io_interface=IOInterface(
            inputs=[
                IO(
                    id=get_uuid_from_seed("component_input_" + input_name),
                    name=input_name,
                    data_type=input_data_type,
                )
                for input_name, input_data_type in main_func.registered_metadata[  # type: ignore
                    "inputs"
                ].items()
            ],
            outputs=[
                IO(
                    id=get_uuid_from_seed("component_output_" + output_name),
                    name=output_name,
                    data_type=output_data_type,
                )
                for output_name, output_data_type in main_func.registered_metadata[  # type: ignore
                    "outputs"
                ].items()
            ],
        ),
        content=component_code,
        test_wiring=WorkflowWiring(),
    )

    tr_json = json.loads(transformation_revision.json())

    return tr_json


##Base function to import a transformation revision from a json file
def import_transformation_from_path(path: str, strip_wirings: bool = False) -> None:
    """
    Imports a transformation revision based on its path on the local system.
    WARNING: Overwrites possible existing transformation revision!
    Args:
        path (str): The local path of the transformation revision.
    Usage:
        import_transformation_from_path(
            "transformations/components/arithmetic/e_100_13d3376a-9c08-d78f-8ad4-6d24fef504ca.json"
        )
    """

    tr_json = load_json(path)

    import_transformation(tr_json, path, strip_wirings=strip_wirings)


def import_transformation(
    tr_json: dict, path: str, strip_wirings: bool = False
) -> None:

    headers = get_auth_headers()

    if strip_wirings:
        tr_json["test_wiring"] = {"input_wirings": [], "output_wirings": []}

    response = requests.put(
        posix_urljoin(
            runtime_config.hd_backend_api_url, "transformations", tr_json["id"]
        )
        + "?allow_overwrite_released=True",
        verify=runtime_config.hd_backend_verify_certs,
        json=tr_json,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )
    logger.info(
        (
            "PUT transformation status code: %d"
            " for transformation %s"
            " of type %s\n"
            "with name %s"
            " in category %s"
        ),
        response.status_code,
        tr_json["id"],
        tr_json["type"],
        tr_json["name"],
        tr_json["category"],
    )
    if response.status_code != 201:
        msg = (
            f"COULD NOT PUT {tr_json['type']} from path {path}\n."
            f"Response status code {response.status_code}"
            f"with response text:\n{response.text}"
        )
        logger.error(msg)


# Import all transformations based on type, id, name and category
def import_transformations(
    download_path: str,
    ids: Optional[List[UUID]] = None,
    names: Optional[List[str]] = None,
    category: Optional[str] = None,
    strip_wirings: bool = False,
) -> None:
    """
    This function imports all transformations together with their documentations
    that match all provided criteria.
    The download_path should be a path which contains the exported transformations
    organized in subdirectories corresponding to the categories.
    WARNING: Overwrites possible existing files!
    Usage:
        import_transformations("./transformations/components")
    """

    path_dict = {}
    transformation_dict = {}

    for root, _, files in os.walk(download_path):
        for file in files:
            path = os.path.join(root, file)
            if path.endswith(".py"):
                logger.info("Loading transformation from python file %s", path)
                python_file = load_python_file(path)
                if python_file:
                    tr_json = transformation_revision_from_python_code(python_file)
                    import_transformation(tr_json, path)
            elif path.endswith(".json"):
                logger.info("Loading transformation from json file %s", path)
                transformation_json = load_json(path)
                transformation_dict[transformation_json["id"]] = transformation_json
                path_dict[transformation_json["id"]] = path
            else:
                logger.warning(
                    "Invalid file extension to loadtransformation revision from: %s",
                    path,
                )

    def nesting_level(transformation_id: UUID, level: int) -> int:

        transformation = transformation_dict[transformation_id]

        level = level + 1
        nextlevel = level

        for operator in transformation["content"]["operators"]:
            if operator["type"] == Type.WORKFLOW:
                logger.info(
                    "workflow %s contains workflow %s -> nesting level %i",
                    str(transformation_id),
                    operator["transformation_id"],
                    level,
                )
                nextlevel = max(
                    nextlevel, nesting_level(operator["transformation_id"], level=level)
                )

        return nextlevel

    level_dict: Dict[int, List[UUID]] = {}

    for transformation_id, transformation in transformation_dict.items():
        level = 0
        if transformation["type"] == Type.WORKFLOW:
            level = nesting_level(transformation_id, level=level)
        if level not in level_dict:
            level_dict[level] = []
        level_dict[level].append(transformation_id)
        logger.info(
            "transformation %s has nesting level %i", str(transformation_id), level
        )

    for level in sorted(level_dict):
        logger.info("importing level %i transformations", level)
        for transformation_id in level_dict[level]:
            transformation = transformation_dict[transformation_id]
            if (
                selection_list_empty_or_contains_value(ids, transformation_id)
                and selection_list_empty_or_contains_value(
                    names, transformation["name"]
                )
                and criterion_unset_or_matches_value(
                    category, transformation["category"]
                )
            ):
                import_transformation_from_path(
                    path_dict[transformation_id], strip_wirings=strip_wirings
                )

    logger.info("finished importing")


def import_all(download_path: str, strip_wirings: bool = False) -> None:
    import_transformations(
        os.path.join(download_path, "components"), strip_wirings=strip_wirings
    )
    import_transformations(
        os.path.join(download_path, "workflows"), strip_wirings=strip_wirings
    )
