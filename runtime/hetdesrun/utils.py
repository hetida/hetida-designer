"""Utilities for scripting and in particular component/workflow deployment"""

import json
import os
import glob
from typing import List, Optional, Tuple, Union, Any, Dict
from pathlib import Path

import importlib

from enum import Enum

from uuid import UUID
import random

import logging
from pydantic import BaseModel  # pylint: disable=no-name-in-module
import requests

from plotly.graph_objects import Figure
from plotly.utils import PlotlyJSONEncoder

from hetdesrun.datatypes import DataType

from hetdesrun.auth.keycloak import KeycloakAccessTokenManager, ServiceUserCredentials

from hetdesrun.service.config import RuntimeConfig

from hetdesrun.component.load import (
    module_path_from_code,
    import_func_from_code,
)

logger = logging.getLogger(__name__)


runtime_config = RuntimeConfig()
# reload actively here for usage in Jupyter notebook where
# env variables may be set before importing this module

kc_access_token_manager = (
    KeycloakAccessTokenManager(
        creds=ServiceUserCredentials(
            realm=runtime_config.hd_keycloak_realm,
            client_id=runtime_config.hd_keycloak_runtime_client_id,
            username=runtime_config.hd_keycloak_runtime_username,
            password=runtime_config.hd_keycloak_runtime_password,
            auth_url=runtime_config.hd_keycloak_auth_url,
            audience=runtime_config.hd_keycloak_runtime_audience,
        )
    )
    if runtime_config.hd_auth_use_keycloak
    else None
)


def get_auth_headers() -> Dict[str, str]:
    return (
        {"Authorization": "Bearer " + kc_access_token_manager.get_access_token()}
        if kc_access_token_manager is not None
        else {}
    )


def get_backend_basic_auth() -> Tuple[Optional[str], Optional[str]]:
    return (
        runtime_config.hd_backend_basic_auth_user,
        runtime_config.hd_backend_basic_auth_password,
    )


def get_uuid_from_seed(seed_str: str) -> UUID:
    """Generate UUID from string

    The seed_str is used to reset the random number generation seed so that this
    function always returns same UUID for the same seed_str.

    This may be used to get reproducible UUIDs from human-readable strings in scripts
    and tests. Should not be used anywhere else for security reasons.
    """
    random.seed(seed_str)
    return UUID(int=random.getrandbits(128))


def load_data(
    json_file: str, md_file: str, code_file: Optional[str] = None
) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """Loads structured and unstructured component / workflow data from files

    Helper function to load a bunch of data from
    * 3 files for a component (a json file, the documentation markdown file, the code file)
    * or from 2 files for a workflow (a json file, the documentation markdown file,).

    Args:
        json_file (str): path to the json file
        md_file (str): path to the documentation markdown file
        code_file (Optional[str], optional): Path to code file. Defaults to None. If None
            this function will only load the json file and the doc file.

    Returns:
        Union[Tuple[Any, str], Tuple[Any, str, str]]: A tuple with structured data
        from json file as first entry, documentation as second entry and if code_file
        is not None the code as third entry. If some part of loading failes, None is returned
    """
    with open(json_file, "r") as f:
        try:
            info = json.load(f)
        except json.JSONDecodeError:
            logger.error("Could not decode %s", json_file)
            info = None
    doc: Optional[str]
    try:
        with open(md_file, "r") as f:
            doc = f.read()
    except FileNotFoundError:
        logger.error("Could not find documentation markdonw file %s", md_file)
        doc = None

    if code_file is None:
        return info, doc, None

    code: Optional[str]
    try:
        with open(code_file, "r") as f:
            code = f.read()
    except FileNotFoundError:
        logger.error("Could not find code file %s", code_file)
        code = None

    return info, doc, code


def file_pathes_from_component_json(
    path_to_component_json: str,
) -> Tuple[str, str, str, str]:
    """Gets all relevant file paths from the component json file path

    This means same basename but .md or .py file extension.

    Args:
        path_to_component_json (str): path to component json file

    Returns:
        Tuple[str, str, str, str]: tuple (base name, json file path, doc path, code file path)
    """

    path_without_ext = os.path.splitext(path_to_component_json)[0]
    base_name = os.path.basename(path_without_ext)
    component_doc_file = path_without_ext + ".md"
    component_code_file = path_without_ext + ".py"
    return base_name, path_to_component_json, component_doc_file, component_code_file


class State(str, Enum):
    """Representing state of component/workflow"""

    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    DISABLED = "DISABLED"


class Type(str, Enum):
    COMPONENT = "COMPONENT"
    WORKFLOW = "WORKFLOW"


class IODTO(BaseModel):
    id: UUID
    name: str
    posX: int = 0
    posY: int = 0
    type: DataType


class ComponentDTO(BaseModel):
    """Component DTO as expected by Backend Service"""

    name: str
    category: str
    code: str
    description: str
    groupId: UUID
    id: UUID
    inputs: List[IODTO]
    outputs: List[IODTO]
    state: State = State.RELEASED
    tag: str
    testInput: dict = {}
    type: Type = Type.COMPONENT


def model_to_pretty_json_str(pydantic_model: BaseModel) -> str:
    """Pretty printing Pydantic Models

    For logging etc.
    """
    return json.dumps(json.loads(pydantic_model.json()), indent=2, sort_keys=True)


def post_component_from_dto(comp_dto: ComponentDTO) -> None:
    logger.debug(
        "JSON Input for Component Controller:\n%s", model_to_pretty_json_str(comp_dto)
    )

    headers = get_auth_headers()

    response = requests.post(
        runtime_config.hd_backend_api_url + "components",
        verify=runtime_config.hd_backend_verify_certs,
        json=json.loads(comp_dto.json()),
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )

    logger.info(
        "component posting status code: %s for component %s",
        str(response.status_code),
        comp_dto.name,
    )
    if response.status_code not in [200, 201]:
        logger.error(
            "COULD NOT POST COMPONENT "
            + comp_dto.name
            + f". Response: {response.status_code} with response text {response.text}"
        )


def post_documentation_from_dto(doc_dto: dict) -> None:
    logger.debug("Putting Component Documentation")

    headers = get_auth_headers()

    response = requests.put(
        runtime_config.hd_backend_api_url + "documentations/" + str(doc_dto["id"]),
        verify=runtime_config.hd_backend_verify_certs,
        json=doc_dto,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )
    logger.info(
        "component documentation posting status code: %s for component %s",
        str(response.status_code),
        str(doc_dto["id"]),
    )
    if response.status_code not in [200, 201]:
        logger.error(
            (
                "COULD NOT PUT COMPONENT DOCUMENTATION %s"
                ". Response: %s with response text %s"
            ),
            str(doc_dto["id"]),
            response.status_code,
            response.text,
        )

def post_component_and_docu_from_python_code(
    code: str, base_name: str, category: Optional[str] = None
) -> None:
    dtos = component_dtos_from_python_code(
        code,
        base_name,
        category,
    )
    
    post_component_from_dto(dtos[0])
    post_documentation_from_dto(dtos[1])


def post_component(
    base_name: str, category: str, info: dict, doc: str, code: str
) -> None:
    """Send component to backend web service for component deployment

    Args:
        base_name (str): A (installation-wide!) unique identifying string for
            the component. UUIDs are generated from this. Should be the base name
            of the files containing the component data.
        category (str): The category under which this component can be found in the
            designer UI.
        info (dict): The structured component data (from the json file)
        doc (str): Markdown documentation content
        code (str): Code module code.
    """

    comp_id = get_uuid_from_seed("component_" + base_name)

    # add IDs to inputs
    info["inputs"] = [
        IODTO(
            **inp,
            id=get_uuid_from_seed("component_input_" + base_name + "_" + inp["name"]),
        )
        for inp in info["inputs"]
    ]

    # add IDs to outputs
    info["outputs"] = [
        IODTO(
            **outp,
            id=get_uuid_from_seed("component_output_" + base_name + "_" + outp["name"]),
        )
        for outp in info["outputs"]
    ]

    comp_dto = ComponentDTO(
        **info,
        category=category.replace("_", " "),
        code=code,
        groupId=comp_id,
        id=comp_id,
        tag="1.0.0"
    )

    post_component_from_dto(comp_dto)

    post_documentation_from_dto({"document": doc, "id": str(comp_id)})

def component_dtos_from_python_code(
    code: str, base_name: str, category: Optional[str] = None
) -> Tuple[ComponentDTO, dict]:
    """Get Component dtos (component, doc) from just the Python code

    This uses information from the register decorator and docstrings to obtain the necessary dtos
    for posting/putting a component and its documentation from just the code.

    Note: This needs to import the code module, which may have arbitrary side effects and security
    implications.

    base_name: A name which is used to derive uuids from. Should be unique over all components!
    """

    main_func = import_func_from_code(code, "main")

    module_path = module_path_from_code(code)
    mod = importlib.import_module(module_path)

    mod_docstring = mod.__doc__ or ""
    mod_docstring_lines = mod_docstring.splitlines()

    component_name = main_func.registered_metadata["name"] or (  # type: ignore
        mod_docstring_lines[0] if mod_docstring_lines[0] != "" else "Unnamed Component"
    )

    component_description = main_func.registered_metadata["description"] or (  # type: ignore
        mod_docstring_lines[0] if mod_docstring_lines[0] != "" else "No description provided"
    )

    component_category = main_func.registered_metadata["category"] or (  # type: ignore
        category.replace("_", " ") if category is not None else "Other"
    )

    component_uuid = main_func.registered_metadata["uuid"] or (  # type: ignore
        get_uuid_from_seed("component_" + base_name)
    )

    component_group_id = main_func.registered_metadata["group_id"] or (  # type: ignore
        get_uuid_from_seed("component_" + base_name)
    )

    component_tag = main_func.registered_metadata["tag"] or (  # type: ignore
        "1.0.0"
    )

    component_code = code.replace(mod_docstring, "", 1)
    component_code = component_code.replace('""""""', "")

    comp_dto = ComponentDTO(
        name=component_name,
        category=component_category,
        code=component_code,
        description=component_description,
        groupId=component_group_id,
        id=component_uuid,
        tag=component_tag,
        inputs=[
            IODTO(
                id=get_uuid_from_seed(
                    "component_input_" + base_name + "_" + input_name
                ),
                name=input_name,
                type=input_data_type,
            )
            for input_name, input_data_type in main_func.registered_metadata[  # type: ignore
                "inputs"
            ].items()
        ],
        outputs=[
            IODTO(
                id=get_uuid_from_seed(
                    "component_output_" + base_name + "_" + output_name
                ),
                name=output_name,
                type=output_data_type,
            )
            for output_name, output_data_type in main_func.registered_metadata[  # type: ignore
                "outputs"
            ].items()
        ],
    )

    documentation_dto = {
        "document": "\n".join(
            mod_docstring_lines[2:]
        ),  # ignore first two lines according to docstring conventions
        "id": str(component_uuid),
    }
    return comp_dto, documentation_dto


def component_dtos_from_python_file(
    path: str, category: Optional[str] = None
) -> Tuple[ComponentDTO, dict]:
    """Get Component dtos (component, doc) from just the Python file

    Wrapper for component_dtos_from_python_code to work on file pathes directly.
    """
    with open(path, "r") as f:
        code = f.read()

    path_without_ext = os.path.splitext(path)[0]
    base_name = os.path.basename(path_without_ext)

    return component_dtos_from_python_code(
        code=code, base_name=base_name, category=category
    )


def post_components_from_directory(base_path_components: str) -> None:
    """Post all components residing in a directory

    This expects a one level hierarchy of subdirectories corresponding to categories,
    i.e. each subdir may contains the files for many components. The subdirectory name
    is used as category for these components. Underscores (_) are turned into spaces.

    IMPORTANT: all component base filenames ever used when
    uploading components this way must be unique since they are used to generate
    the component uuid.
    """
    try:
        (_, categories, _) = next(os.walk(base_path_components))
    except StopIteration:
        logger.warning(
            "No Components in directory %s found for posting!",
            base_path_components,
        )
        return

    handled_base_names = set()
    for category in categories:

        # find all json files (each represents one component)
        component_json_files = glob.glob(
            os.path.join(base_path_components, category, "*.json")
        )

        for component_json_file in component_json_files:
            # get other files (doc, code)
            path_without_ext = os.path.splitext(component_json_file)[0]
            base_name = os.path.basename(path_without_ext)

            if base_name in handled_base_names:
                logger.warning(
                    (
                        "The component file base_name %s has already been posted!"
                        " So we skip posting  component from %s"
                    ),
                    base_name,
                    component_json_file,
                )
                continue

            component_doc_file = path_without_ext + ".md"
            component_code_file = path_without_ext + ".py"
            logger.info("##### Uploading Component %s", base_name)
            logger.debug(
                "File paths:\n%s",
                "\n".join(
                    [component_json_file, component_doc_file, component_code_file]
                ),
            )

            info, doc, code = load_data(
                component_json_file, component_doc_file, component_code_file
            )
            if None in [info, doc, code]:
                raise ValueError(
                    "Data for component not provided completely"
                    + str((info, doc, code))
                )

            assert info is not None  # for mypy # nosec
            assert doc is not None  # for mypy # nosec
            assert code is not None  # for mypy # nosec

            post_component(base_name, category, info, doc, code)

            handled_base_names.add(base_name)
        component_py_files = [
            path
            for path in glob.glob(os.path.join(base_path_components, category, "*.py"))
            if (
                (not os.path.basename(path).startswith("test_"))
                and (not os.path.basename(path) == "__init__.py")
            )
        ]

        for component_py_file in component_py_files:
            path_without_ext = os.path.splitext(component_py_file)[0]
            base_name = os.path.basename(path_without_ext)
            if base_name not in handled_base_names:
                comp_dto, doc_dto = component_dtos_from_python_file(
                    component_py_file, category=category
                )
                post_component_from_dto(comp_dto)

                post_documentation_from_dto(doc_dto)
                handled_base_names.add(base_name)


def download_workflow_to_files(
    id: Union[UUID, str], base_path_workflows: str  # pylint: disable=redefined-builtin
) -> None:
    """Downloads a workflow and its documentation and saves that to files

    WARNING: Overwrites possible existing files!

    This downloads the workflow with the given id from the backend web
    service.

    Workflow is downloaded to a directory corresponding to the workflow category which
    is created as a subdir of the given base_path_workflows directory.

    Usage:
        download_workflow_to_files("5e2d5320-db5a-4430-b0a7-700abc508adb", "./workflows")
    """
    headers = get_auth_headers()

    response = requests.get(
        runtime_config.hd_backend_api_url + "workflows/" + str(id),
        verify=runtime_config.hd_backend_verify_certs,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )
    wf_json = response.json()

    doc_response = requests.get(
        runtime_config.hd_backend_api_url + "documentations/" + str(id),
        verify=runtime_config.hd_backend_verify_certs,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        headers=headers,
    )

    doc_text = doc_response.json().get("document", "")

    cat_for_dir = wf_json["category"].replace(" ", "_")
    cat_dir = os.path.join(base_path_workflows, cat_for_dir)

    logger.info("Store to: %s", cat_dir)
    name_for_filenames = wf_json["name"].replace(" ", "_")

    # create category directory
    Path(cat_dir).mkdir(parents=True, exist_ok=True)

    # write json file
    with open(os.path.join(cat_dir, name_for_filenames + ".json"), "w") as f:
        json.dump(wf_json, f, indent=2, sort_keys=True)

    # write documentation file
    with open(os.path.join(cat_dir, name_for_filenames + ".md"), "w") as f:
        f.write(doc_text)


def post_workflow(json_info: dict, doc: str) -> None:

    headers = get_auth_headers()

    response = requests.put(
        runtime_config.hd_backend_api_url + "workflows/" + json_info["id"],
        verify=runtime_config.hd_backend_verify_certs,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        json=json_info,
        headers=headers,
    )

    logger.info(
        "Workflow posting status code: %s, %s",
        response.status_code,
        response.text,
    )

    if response.status_code not in [200, 201]:
        logger.error(
            "COULD NOT POST WORKFLOW "
            + json_info["id"]
            + f". Response: {response.status_code} with response text {response.text}"
        )

    response = requests.put(
        runtime_config.hd_backend_api_url + "documentations/" + json_info["id"],
        verify=runtime_config.hd_backend_verify_certs,
        auth=get_backend_basic_auth()
        if runtime_config.hd_backend_use_basic_auth
        else None,
        json={"id": json_info["id"], "document": doc},
        headers=headers,
    )

    logger.info(
        "Workflow documentation posting status code: %s, %s",
        str(response.status_code),
        response.text,
    )

    if response.status_code not in [200, 201]:
        logger.error(
            "COULD NOT PUT WORKFLOW DOCUMENTATION "
            + json_info["id"]
            + f". Response: {response.status_code} with response text {response.text}"
        )


def post_workflows_from_directory(base_path_workflows: str) -> None:
    try:
        (_, categories, _) = next(os.walk(base_path_workflows))
    except StopIteration:
        logger.warning(
            "No Workflows in directory %s found for posting!",
            base_path_workflows,
        )
        return
    for category in categories:
        workflow_json_files = glob.glob(
            os.path.join(base_path_workflows, category, "*.json")
        )

        for workflow_json_file in workflow_json_files:
            path_without_ext = os.path.splitext(workflow_json_file)[0]
            base_name = os.path.basename(path_without_ext)

            workflow_doc_file = path_without_ext + ".md"

            logger.info("##### Uploading Workflow %s", base_name)
            logger.debug(
                "File paths:\n%s", "\n".join([workflow_json_file, workflow_doc_file])
            )

            info, doc, _ = load_data(workflow_json_file, workflow_doc_file)

            if None in [info, doc]:
                raise ValueError(
                    "Data for workflow not provided completely" + str((info, doc))
                )
            assert info is not None  # for mypy # nosec
            assert doc is not None  # for mypy # nosec
            post_workflow(info, doc)


def plotly_fig_to_json_dict(fig: Figure) -> Any:
    """Turn Plotly figure into a Python dict-like object

    This function can be used in visualization components to obtain the
    correct plotly json-like object from a Plotly Figure object.

    See visualization components from the accompanying base components for
    examples on usage.
    """
    # possibly quite inefficient (multiple serialisation / deserialization) but
    # guarantees that the PlotlyJSONEncoder is used and so the resulting Json
    # should be definitely compatible with the plotly javascript library:
    return json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))
