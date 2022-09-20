import importlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from hetdesrun.component.load import (
    ComponentCodeImportError,
    import_func_from_code,
    module_path_from_code,
)
from hetdesrun.exportimport.purge import deprecate_all_but_latest_in_group
from hetdesrun.exportimport.utils import update_or_create_transformation_revision
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IO, IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type, get_uuid_from_seed

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


def get_transformation_revisions_from_path(
    download_path: str,
) -> Dict[UUID, TransformationRevision]:
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
            try:
                transformation = TransformationRevision(**transformation_json)
            except ValueError as err:
                logger.error(
                    "ValueError for json from path %s:\n%s", download_path, str(err)
                )
            else:
                transformation_dict[transformation.id] = transformation

    return transformation_dict


def import_transformations(
    download_path: str,
    strip_wirings: bool = False,
    directly_into_db: bool = False,
    update_component_code: bool = True,
    deprecate_older_revisions: bool = False,
) -> None:
    """Import all transforamtions from specified download path.

    This function imports all transformations together with their documentations.
    The download_path should be a path which contains the exported transformations
    organized in subdirectories corresponding to the categories.
    The following parameters can be used to

    - directly_into_db: If direct access to the database is possible, set this to true
        to ommit the detour via the backend
    - strip_wirings: Set to true to reset the test wiring to empty input and output
        wirings for each transformation revision
    - update_component_code: Set to false if you want to keep the componen code
        unchanged
    - deprecate_older_versions: Set to true to deprecate all but the latest revision
        for all revision groups imported. This might result in all imported revisions to
        be deprecated if these are older than the latest revision in the database.

    WARNING: Overwrites possibly existing transformation revisions!

    Usage:
        import_transformations("./transformations/components")
    """

    transformation_dict = get_transformation_revisions_from_path(download_path)

    def nesting_level(transformation_id: UUID, level: int) -> int:

        transformation = transformation_dict[transformation_id]

        if transformation.type == Type.COMPONENT:
            return level

        level = level + 1
        nextlevel = level
        assert isinstance(transformation.content, WorkflowContent)
        for operator in transformation.content.operators:
            if operator.type == Type.WORKFLOW:
                logger.info(
                    "transformation %s contains workflow %s at nesting level %i",
                    str(transformation_id),
                    operator.transformation_id,
                    level,
                )
                nextlevel = max(
                    nextlevel, nesting_level(operator.transformation_id, level=level)
                )

        return nextlevel

    level_dict: Dict[int, List[UUID]] = {}

    for transformation_id, transformation in transformation_dict.items():
        level = nesting_level(transformation_id, level=0)
        if level not in level_dict:
            level_dict[level] = []
        level_dict[level].append(transformation_id)
        logger.info(
            "transformation %s of type %s has nesting level %i",
            str(transformation_id),
            transformation.type,
            level,
        )

    for level in sorted(level_dict):
        logger.info("importing level %i transformations", level)
        for transformation_id in level_dict[level]:
            transformation = transformation_dict[transformation_id]
            if strip_wirings:
                transformation.test_wiring = WorkflowWiring()
            update_or_create_transformation_revision(
                transformation,
                directly_into_db=directly_into_db,
                update_component_code=update_component_code,
            )

    logger.info("finished importing")

    if deprecate_older_revisions:
        revision_group_ids = set(
            transformation.revision_group_id
            for _, transformation in transformation_dict.items()
        )
        logger.info("deprecate all but latest revision of imported revision groups")
        for revision_group_id in revision_group_ids:
            deprecate_all_but_latest_in_group(
                revision_group_id, directly_into_db=directly_into_db
            )
