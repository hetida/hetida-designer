"""Utilities for loading ensembles of transformation revisions from disk"""

import json
import logging
import os
from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pandas as pd
from pydantic import BaseModel, Field, StrictInt, StrictStr, parse_file_as

from hetdesrun.component.code_utils import (
    CodeParsingException,
    get_global_from_code,
    get_module_doc_string,
)
from hetdesrun.component.load import (
    ComponentCodeImportError,
)
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    TransformationInput,
    TransformationOutput,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.save import save_transformation_into_directory
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


def load_python_file(path: str) -> str | None:
    """Load pyython code from a file

    Returns None if file is not found, the contained code as str otherwise.
    """
    try:
        with open(path, encoding="utf8") as f:
            python_code = f.read()
    except FileNotFoundError:
        logger.error("Could not find python file at path %s", path)
        python_code = None
    return python_code


def get_json_default_value_from_python_object(input_info: dict) -> str | None:
    if "default_value" not in input_info or input_info["default_value"] is None:
        return None

    if "data_type" not in input_info:
        raise ValueError("For optional inputs a data type must be provided in the COMPONENT_INFO!")

    if isinstance(input_info["default_value"], str) and input_info["data_type"] in (
        "STRING",
        "ANY",
    ):
        return input_info["default_value"]

    if isinstance(input_info["default_value"], pd.Series | pd.DataFrame) and input_info[
        "data_type"
    ] in ("SERIES", "DATAFRAME", "MULTITSFRAME"):
        return str(input_info["default_value"].to_json(date_format="iso"))

    return json.dumps(input_info["default_value"])


def transformation_revision_from_python_code(code: str) -> TransformationRevision:  # noqa: PLR0915
    """Get the TransformationRevision as a json-like object from just the Python code

    This uses information from the register decorator or a global variable COMPONENT_INFO
    and docstrings.

    Note: This needs to import the provided code, which may have arbitrary side effects
    and security implications.
    """
    try:
        mod_docstring = get_module_doc_string(code) or ""
    except CodeParsingException as e:
        msg = f"Could not parse component code:\n{str(e)}"
        logging.debug(msg)
        raise ComponentCodeImportError(msg) from e

    mod_docstring_lines = mod_docstring.splitlines()
    component_documentation = "\n".join(mod_docstring_lines[2:])

    default_dict = {
        "inputs": {},
        "outputs": {},
        "name": "Unnamed Component",
        "description": "No description provided",
        "category": "Other",
        "version_tag": "1.0.0",
        "id": uuid4(),
        "revision_group_id": uuid4(),
        "state": "RELEASED",
    }

    try:
        component_info_dict = get_global_from_code(
            code,
            "COMPONENT_INFO",
            default_value=default_dict,
        )
    except CodeParsingException as e:
        msg = (
            f"Could not parse component code for extracting component info:\n{str(e)}."
            " Proceeding with default values."
        )
        logging.debug(msg)
        component_info_dict = default_dict
        raise ComponentCodeImportError(msg) from e

    new_dict = deepcopy(default_dict)
    new_dict.update(component_info_dict)
    component_info_dict = new_dict

    component_info_dict["released_timestamp"] = component_info_dict.get(
        "released_timestamp",
        (
            datetime.now(timezone.utc).isoformat()
            if component_info_dict["state"] != "DRAFT"
            else None
        ),
    )
    component_info_dict["disabled_timestamp"] = component_info_dict.get(
        "disabled_timestamp",
        (
            datetime.now(timezone.utc).isoformat()
            if component_info_dict["state"] == "DISABLED"
            else None
        ),
    )

    try:
        test_wiring_dict = get_global_from_code(
            code, "TEST_WIRING_FROM_PY_FILE_IMPORT", default_value={}
        )
    except CodeParsingException as e:
        msg = (
            f"Could not parse component code for extracting test wiring:\n{str(e)}."
            " Defaulting to empty wiring"
        )
        logging.warning(msg)
        test_wiring_dict = {}
    if len(test_wiring_dict) == 0:
        logger.debug("Test wiring extraction result is an empty test wiring.")

    try:
        test_wiring = WorkflowWiring(**test_wiring_dict)
    except ValueError as error:
        logger.warning("The dictionary cannot be parsed as WorkflowWiring:\n%s", str(error))
        test_wiring = WorkflowWiring()

    try:
        release_wiring_dict = get_global_from_code(code, "RELEASE_WIRING", default_value=None)
    except CodeParsingException as e:
        msg = (
            f"Could not parse component code for extracting release wiring:\n{str(e)}."
            " Defaulting to empty wiring (None)"
        )
        logging.warning(msg)
        release_wiring_dict = None

    if release_wiring_dict is not None:
        if len(release_wiring_dict) == 0:
            logger.debug("Release wiring extraction result is an empty wiring.")

        try:
            release_wiring = WorkflowWiring(**release_wiring_dict)
        except ValueError as error:
            logger.warning("The dictionary cannot be parsed as WorkflowWiring:\n%s", str(error))
            release_wiring = None

    else:
        release_wiring = None

    transformation_revision = TransformationRevision(
        **component_info_dict,
        type=Type.COMPONENT,
        documentation=component_documentation,
        io_interface=IOInterface(
            inputs=[
                TransformationInput(
                    id=get_uuid_from_seed("component_input_" + input_name),
                    name=input_name,
                    data_type=(
                        input_info["data_type"]
                        if isinstance(input_info, dict) and "data_type" in input_info
                        else input_info
                    ),
                    # input info maybe a datatype string (backwards compatibility)
                    # or a dictionary containing the datatype as well as a potential default value
                    value=get_json_default_value_from_python_object(input_info),
                    type=(
                        InputType.OPTIONAL
                        if isinstance(input_info, dict) and "default_value" in input_info
                        else InputType.REQUIRED
                    ),
                )
                for input_name, input_info in component_info_dict["inputs"].items()
            ],
            outputs=[
                TransformationOutput(
                    id=get_uuid_from_seed("component_output_" + output_name),
                    name=output_name,
                    data_type=(
                        output_info["data_type"]
                        if isinstance(output_info, dict) and "data_type" in output_info
                        else output_info
                    ),
                    # input info maybe a datatype string (backwards compatibility)
                    # or a dictionary containing the datatype
                )
                for output_name, output_info in component_info_dict["outputs"].items()
            ],
        ),
        content=code,
        test_wiring=test_wiring,
        release_wiring=release_wiring,
    )

    return transformation_revision


def load_transformation_revisions_from_directory(  # noqa: PLR0912
    download_path: str, transform_py_to_json: bool = False
) -> tuple[dict[UUID, TransformationRevision], dict[UUID, str]]:
    transformation_dict: dict[UUID, TransformationRevision] = {}
    path_dict: dict[UUID, str] = {}

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
                        transformation = transformation_revision_from_python_code(python_code)
                    except ComponentCodeImportError as e:
                        logging.error(
                            "Could not load main function from %s\n"
                            "due to error during import of component code:\n%s",
                            path,
                            str(e),
                        )
                        continue

            if ext == ".json":
                logger.info("Loading transformation from json file %s", path)
                transformation_json = load_json(path)
                try:
                    transformation = TransformationRevision(**transformation_json)
                except ValueError as err:
                    logger.error("ValueError for json from path %s:\n%s", download_path, str(err))
                    continue
            transformation_dict[transformation.id] = transformation
            if ext == ".py":
                if transform_py_to_json:
                    path = save_transformation_into_directory(
                        transformation_revision=transformation,
                        directory_path=download_path,
                    )
                    path_dict[transformation.id] = path
                path_dict[transformation.id] = path
            else:
                path_dict[transformation.id] = path

    return transformation_dict, path_dict


def load_trafos_from_trafo_list_json_file(
    path: str,
) -> list[TransformationRevision]:
    """Load trafo rev list from a json file

    For example the json of api/transformations GET endpoint response written into
    a file is a valid input for this function.
    """

    trafo_revisions = parse_file_as(list[TransformationRevision], path)
    return trafo_revisions


class ImportSource(BaseModel):
    path: str
    is_dir: bool
    config_file: str | None


class MultipleTrafosUpdateConfig(BaseModel):
    """Config for updating multiple trafo revisions"""

    allow_overwrite_released: bool = Field(
        False,
        description=(
            "Warning: Setting this to True may destroy depending transformation revisions"
            " and seriously limit reproducibility."
        ),
    )
    update_component_code: bool = Field(
        True,
        description=(
            "Automatically updates component code to newest structure."
            " This should be harmless for components created in hetida designer."
        ),
    )
    strip_wirings: bool = Field(
        False,
        description=(
            "Whether test wirings should be removed before importing."
            "This can be necessary if an adapter used in a test wiring is not "
            "available on this system."
        ),
    )
    strip_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Field(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " test wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_wirings this allows to"
        " fine-granulary exclude only those parts of test wirings corresponding to"
        " adapters which are not present.",
    )
    keep_only_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Field(
        set(),
        description="In each test wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_wirings"
        " if you actually want to remove all wirings in the test wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the test wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation.",
    )
    strip_release_wirings: bool = Field(
        False,
        description=(
            "Whether release wirings should be removed before importing."
            "This can be necessary if an adapter used in a release wiring is not "
            "available on this system."
        ),
    )
    strip_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Field(
        set(),
        description="Remove all input wirings and output wirings from the trafo's"
        " release wiring with this adapter id. Can be provided multiple times."
        " In contrast to strip_release_wirings this allows to"
        " fine-granulary exclude only those parts of release wirings corresponding to"
        " adapters which are not present.",
    )
    keep_only_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] = Field(
        set(),
        description="In each release wiring keep only the input wirings and output wirings"
        " with the given adapter id. Can be set multiple times and then only wirings with"
        " any of the given ids are kept. If not set, this has no effect (use strip_release_wirings"
        " if you actually want to remove all wirings in the release wiring). A typical case"
        " is when you want to only keep the wirings with adapter id direct_provisioning,"
        " i.e. manual inputs of the release wiring, in order to remove dependencies from"
        " external adapters not present on the target hetida designer installation.",
    )
    abort_on_error: bool = Field(
        False,
        description=(
            "If updating/creating fails for some trafo revisions and this setting is true,"
            " no attempt will be made to update/create the remaining trafo revs."
            " Note that the order in which updating/creating happens may differ from"
            " the ordering of the provided list since they are ordered by dependency"
            " relation before trying to process them. So it may be difficult to determine."
            " which trafos have been skipped / are missing and which have been successfully"
            " processed. Note that already processed actions will not be reversed."
        ),
    )
    deprecate_older_revisions: bool = Field(
        False,
        description=(
            "Whether older revisions in the same trafo revision group should be deprecated."
            " If this is True, this is done for every revision group for which any trafo"
            " rev passes the filters and even for those that are included as dependencies"
            " via the include_dependencies property of the filter params!"
            " Note that this might not be done if abort_on_error is True and there is"
            " an error anywhere."
        ),
    )


class ImportSourceConfig(BaseModel):
    filter_params: FilterParams
    update_config: MultipleTrafosUpdateConfig


def get_import_sources(directory_path: str) -> Iterable[ImportSource]:  # noqa: PLR0912
    """Get all import sources inside a directory

    Note: Does not parse/validate import sources.
    """

    import_sources: dict[str, dict[str, str | None | bool]] = {}
    for sub_element in os.listdir(directory_path):
        sub_path = os.path.join(directory_path, sub_element)

        if os.path.isdir(sub_path):
            try:
                existing_info = import_sources[sub_path]
                existing_info["is_dir"] = True
            except KeyError:
                existing_info = {"is_dir": True, "config_file": None}

            import_sources[sub_path] = existing_info

        elif os.path.isfile(sub_path):
            if sub_path.endswith(".config.json"):
                original_path = sub_path.removesuffix(".config.json")
                try:
                    existing_info = import_sources[original_path]
                    existing_info["config_file"] = sub_path
                except KeyError:
                    existing_info = {"is_dir": None, "config_file": sub_path}
                import_sources[original_path] = existing_info

            elif sub_path.endswith(".json"):
                try:
                    existing_info = import_sources[sub_path]
                    existing_info["is_dir"] = False
                except KeyError:
                    existing_info = {"is_dir": False, "config_file": None}
                import_sources[sub_path] = existing_info

            else:
                logger.warning(
                    "Unknown file format in import directory %s: %s",
                    directory_path,
                    sub_path,
                )

    for target_path, import_source in import_sources.items():
        if import_source["is_dir"] is None:
            logger.warning(
                "Found config file for target but no target: %s",
                import_source["config_file"],
            )
        else:
            yield ImportSource(
                path=target_path,
                is_dir=import_source["is_dir"],
                config_file=import_source["config_file"],
            )


class Importable(BaseModel):
    transformation_revisions: list[TransformationRevision]
    import_config: ImportSourceConfig


def load_import_source(
    import_source: ImportSource,
) -> Importable:
    # Get import config
    if import_source.config_file is None:
        import_config = ImportSourceConfig(
            filter_params=FilterParams(), update_config=MultipleTrafosUpdateConfig()
        )
    else:
        import_config = ImportSourceConfig.parse_file(import_source.config_file)

    # Load trafo revisions
    if import_source.is_dir:
        trafo_revisions_dict, _ = load_transformation_revisions_from_directory(import_source.path)
        trafo_revisions = list(trafo_revisions_dict.values())
    else:
        trafo_revisions = load_trafos_from_trafo_list_json_file(import_source.path)

    return Importable(transformation_revisions=trafo_revisions, import_config=import_config)


def load_import_sources(import_sources: Iterable[ImportSource]) -> list[Importable]:
    return [load_import_source(import_source) for import_source in import_sources]


def load_import_sources_from_directory(directory_path: str) -> list[Importable]:
    return load_import_sources(get_import_sources(directory_path=directory_path))
