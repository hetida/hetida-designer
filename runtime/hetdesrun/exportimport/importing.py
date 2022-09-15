import importlib
import json
import logging
import os
from datetime import datetime, timezone
from posixpath import join as posix_urljoin
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

import requests

from hetdesrun.component.load import (
    ComponentCodeImportError,
    import_func_from_code,
    module_path_from_code,
)
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.dbservice.revision import (
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.io import IO, IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import (
    State,
    Type,
    criterion_unset_or_matches_value,
    get_backend_basic_auth,
    get_uuid_from_seed,
    selection_list_empty_or_contains_value,
)
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def load_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            workflow_json = json.load(f)
    except FileNotFoundError:
        logger.error("Could not find json file at path %s", path)
        workflow_json = None
    return workflow_json


def load_python_file(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            python_file = f.read()
    except FileNotFoundError:
        logger.error("Could not find python file at path %s", path)
        python_file = None
    return python_file


def transformation_revision_from_python_code(code: str, path: str) -> Any:
    """Get the TransformationRevision as a json file from just the Python code of some component
    This uses information from the register decorator and docstrings.
    Note: This needs to import the code module, which may have arbitrary side effects and security
    implications.
    """

    try:
        main_func = import_func_from_code(code, "main")
    except ComponentCodeImportError as e:
        logging.error(
            "Could not load function from %s\n"
            "due to error during import of component code:\n%s",
            path,
            str(e),
        )

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

        component_id = main_func.registered_metadata["id"] or (  # type: ignore
            get_uuid_from_seed(str(component_name))
        )

        component_group_id = main_func.registered_metadata["revision_group_id"] or (  # type: ignore
            get_uuid_from_seed(str(component_name))
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
        component_id = info_dict.get("id", get_uuid_from_seed(str(component_name)))
        component_group_id = info_dict.get(
            "revision_group_id", get_uuid_from_seed(str(component_name))
        )
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


# Base function to import a transformation revision
def import_transformation(
    tr_json: dict,
    path: str,
    strip_wirings: bool = False,
    directly_into_db: bool = False,
    update_component_code: bool = True,
) -> None:

    if strip_wirings:
        tr_json["test_wiring"] = {"input_wirings": [], "output_wirings": []}

    if directly_into_db:
        tr = TransformationRevision(**tr_json)
        logger.info(
            (
                "Update or create database entry"
                " for transformation revision %s of type %s\n"
                "in category %s with name %s"
            ),
            str(tr.id),
            str(tr.type),
            tr.category,
            tr.name,
        )
        update_or_create_single_transformation_revision(tr)

    else:
        headers = get_auth_headers()

        response = requests.put(
            posix_urljoin(
                get_config().hd_backend_api_url, "transformations", tr_json["id"]
            ),
            params={
                "allow_overwrite_released": True,
                "update_component_code": update_component_code,
            },
            verify=get_config().hd_backend_verify_certs,
            json=tr_json,
            auth=get_backend_basic_auth()  # type: ignore
            if get_config().hd_backend_use_basic_auth
            else None,
            headers=headers,
            timeout=get_config().external_request_timeout,
        )
        logger.info(
            (
                "PUT transformation status code: %d"
                " for transformation revision %s of type %s\n"
                "in category %s with name %s"
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


# Import all transformations from download_path based on type, id, name and category
def import_transformations(
    download_path: str,
    type: Optional[Type] = None,  # pylint: disable=redefined-builtin
    state: Optional[State] = None,
    ids: Optional[List[UUID]] = None,
    names_and_tags: Optional[List[Tuple[str, str]]] = None,
    category: Optional[str] = None,
    strip_wirings: bool = False,
    directly_into_db: bool = False,
    update_component_code: bool = True,
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
                python_file = load_python_file(path)
                if python_file is not None:
                    transformation_json = transformation_revision_from_python_code(
                        python_file, path
                    )
            if ext == ".json":
                logger.info("Loading transformation from json file %s", path)
                transformation_json = load_json(path)
            transformation_dict[transformation_json["id"]] = transformation_json
            path_dict[transformation_json["id"]] = path

    def nesting_level(transformation_id: UUID, level: int) -> int:

        transformation = transformation_dict[transformation_id]

        level = level + 1
        nextlevel = level

        for operator in transformation["content"]["operators"]:
            if operator["type"] == Type.WORKFLOW:
                logger.info(
                    "transformation %s contains workflow %s at nesting level %i",
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
            "transformation %s of type %s has nesting level %i",
            str(transformation_id),
            transformation["type"],
            level,
        )

    for level in sorted(level_dict):
        logger.info("importing level %i transformations", level)
        for transformation_id in level_dict[level]:
            transformation = transformation_dict[transformation_id]
            if (
                criterion_unset_or_matches_value(type, transformation["type"])
                and criterion_unset_or_matches_value(state, transformation["state"])
                and selection_list_empty_or_contains_value(ids, transformation_id)
                and selection_list_empty_or_contains_value(
                    names_and_tags,
                    (transformation["name"], transformation["version_tag"]),
                )
                and criterion_unset_or_matches_value(
                    category, transformation["category"]
                )
            ):
                import_transformation(
                    transformation,
                    path_dict[transformation_id],
                    strip_wirings=strip_wirings,
                    directly_into_db=directly_into_db,
                    update_component_code=update_component_code,
                )

    logger.info("finished importing")
