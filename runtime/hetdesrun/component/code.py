"""Code template generation

This module contains functions for generating and updating component code modules
to provide a very elementary support system to the designer code editor.
"""

import json
import logging
from keyword import iskeyword

import black

from hetdesrun.component.code_utils import (
    CodeParsingException,
    format_code_with_black,
    update_module_level_variable,
)
from hetdesrun.datatypes import (
    DataType,
    parse_single_value_dynamically,
)
from hetdesrun.persistence.models.io import InputType, TransformationInput
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)

imports_template: str = """\
# add your own imports here, e.g.
# import pandas as pd
# import numpy as np


"""

function_definition_template: str = """\
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {{
    "inputs": {input_dict_content},
    "outputs": {output_dict_content},
    "name": {name},
    "category": {category},
    "description": {description},{description_too_long_noqa}
    "version_tag": {version_tag},
    "id": {id},
    "revision_group_id": {revision_group_id},
    "state": {state},{timestamp}
}}

from hdutils import parse_default_value  # noqa: E402, F401

{main_func_declaration_start} main({params_list}):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
"""

function_body_template: str = """
    # write your function code here.
    pass
"""


def component_info_default_value_string(inp: TransformationInput) -> str:
    if inp.value == "" and inp.data_type not in (DataType.String, DataType.Any):
        return repr(None)

    if inp.data_type in (DataType.Series, DataType.DataFrame, DataType.MultiTSFrame):
        return repr(
            parse_single_value_dynamically(
                name=inp.name if inp.name is not None else "UNKNOWN",
                value=inp.value,
                data_type=DataType.Any,  # to get an object corresponding to the json
                nullable=True,
            )
        )

    try:
        return repr(
            parse_single_value_dynamically(
                name=inp.name if inp.name is not None else "UNKNOWN",
                value=inp.value,
                data_type=inp.data_type,
                nullable=True,
            )
        )
    except ValueError as error:
        msg = (
            f"Parsing Error for value '{inp.value}' of input '{inp.name}' as {inp.data_type.value}"
            + (f":\n{str(error)}" if inp.value != "None" else ". Enter 'null' instead.")
        )
        logger.error(msg)
        raise TypeError(msg) from error


def function_signature_default_value_string(inp: TransformationInput) -> str:
    if inp.value == "" and inp.data_type not in (DataType.String, DataType.Any):
        return repr(None)

    if inp.data_type in (
        DataType.Series,
        DataType.DataFrame,
        DataType.MultiTSFrame,
        DataType.Any,
    ):
        if not inp.data_type is DataType.Any and not isinstance(
            inp.value, str | dict | list | None
        ):
            msg = (
                f"Default value '{inp.value}' of input '{inp.name}' "
                f"has wrong type for a {inp.data_type}."
            )
            logger.error(msg)
            raise TypeError(msg)
        return f'parse_default_value(COMPONENT_INFO, "{inp.name}")'

    try:
        return repr(
            parse_single_value_dynamically(
                name=inp.name if inp.name is not None else "UNKNOWN",
                value=inp.value,
                data_type=inp.data_type,
                nullable=True,
            )
        )
    except ValueError as error:
        msg = (
            f"Parsing Error for value '{inp.value}' of input '{inp.name}' as {inp.data_type.value}"
            + (f":\n{str(error)}" if inp.value != "None" else ". Enter 'null' instead.")
        )
        logger.error(msg)
        raise TypeError(msg) from error


def format_function_header(function_header: str) -> str:
    # add function_body_template to fulfill indented block expectation after function definition
    formatted_function_header_with_body_template = format_code_with_black(
        function_header + function_body_template
    )
    # remove function_body_template again
    formatted_function_header = formatted_function_header_with_body_template.removesuffix(
        function_body_template
    )
    return formatted_function_header


def description_too_long(description: str) -> bool:
    # max_line length = 100
    # overhead length = len('    "description": "",')
    # max description length = max line length - overhead length = 77
    return len(description) > 77


def default_value_part(inp: TransformationInput) -> str:
    if inp.type != InputType.OPTIONAL:
        return ""

    try:
        default_value_rep_part = component_info_default_value_string(inp)
    except TypeError as e:
        msg = (
            f"Could not generate default value string representation for input {inp.name}."
            f" Error was:\n{str(e)}"
        )
        logger.warning(msg)
        return ""

    return ', "default_value": ' + default_value_rep_part


def generate_function_header(component: TransformationRevision, is_coroutine: bool = False) -> str:
    """Generate entrypoint function header from the inputs and their types"""
    param_list_str = (
        ""
        if len(component.io_interface.inputs) == 0
        else "*, "
        + ", ".join(
            [
                inp.name
                for inp in component.io_interface.inputs
                if inp.type == InputType.REQUIRED and inp.name is not None
            ]
            + [
                inp.name + "=" + function_signature_default_value_string(inp)
                for inp in component.io_interface.inputs
                if inp.type == InputType.OPTIONAL and inp.name is not None
            ]
        )
    )

    main_func_declaration_start = "async def" if is_coroutine else "def"

    input_dict_str = (
        "{"
        + ("\n    " if len(component.io_interface.inputs) != 0 else "")
        + "".join(
            [
                '    "'
                + inp.name
                + '": {"data_type": "'
                + inp.data_type.value
                + '"'
                + (default_value_part(inp))
                + "},\n    "
                for inp in component.io_interface.inputs
                if inp.name is not None
            ]
        )
        + "}"
    )

    output_dict_str = (
        "{"
        + ("\n    " if len(component.io_interface.outputs) != 0 else "")
        + "".join(
            [
                '    "' + output.name + '": {"data_type": "' + output.data_type.value + '"},\n    '
                for output in component.io_interface.outputs
                if output.name is not None
            ]
        )
        + "}"
    )

    timestamp_str = ""

    if component.state == State.RELEASED:
        if component.released_timestamp is None:
            raise TypeError("released timestamp must be set for a released component")
        timestamp_str = "\n    " + '"released_timestamp": "'  # noqa: ISC003
        timestamp_str = timestamp_str + component.released_timestamp.isoformat()
        timestamp_str = timestamp_str + '",'

    if component.state == State.DISABLED:
        if component.released_timestamp is None:
            raise TypeError("released timestamp must be set for a disabled component")
        timestamp_str = "\n    " + '"released_timestamp": "'  # noqa: ISC003
        timestamp_str = timestamp_str + component.released_timestamp.isoformat()
        timestamp_str = timestamp_str + '",'
        if component.disabled_timestamp is None:
            raise TypeError("disabled timestamp must be set for a disabled component")
        timestamp_str = timestamp_str + "\n    " + '"disabled_timestamp": "'
        timestamp_str = timestamp_str + component.disabled_timestamp.isoformat()
        timestamp_str = timestamp_str + '",'

    function_header = function_definition_template.format(
        input_dict_content=input_dict_str,
        output_dict_content=output_dict_str,
        name='"' + component.name + '"',
        description='"' + component.description + '"',
        description_too_long_noqa=(
            "  # noqa: E501" if description_too_long(component.description) else ""
        ),
        category='"' + component.category + '"',
        version_tag='"' + component.version_tag + '"',
        id='"' + str(component.id) + '"',
        revision_group_id='"' + str(component.revision_group_id) + '"',
        state='"' + component.state + '"',
        timestamp=timestamp_str,
        params_list=param_list_str,
        main_func_declaration_start=main_func_declaration_start,
    )

    try:
        return format_function_header(function_header)
    except black.InvalidInput as error:
        logger.warning(
            "Error while generating function header for compoent %s:\n%s",
            str(component.id),
            str(error),
        )
        return function_header

    return format_code_with_black(function_header)


def generate_complete_component_module(
    component: TransformationRevision, is_coroutine: bool = False
) -> str:
    return (
        imports_template
        + "# %%\n"
        + generate_function_header(component, is_coroutine)
        + function_body_template
        + "\n\n# %%\n"
    )


def update_code(
    tr: TransformationRevision,
) -> str:
    """Generate and update component code

    Tries to replace the existing_code with a new version with the correct function definition
    from input_type_dict and output_type_dict.
    If no existing_code is provided it completely generates a component module code stub
    including necessary imports.

    The updating process is rather naive: It does not rely on parsing the abstract syntax tree.
    It only uses basic String methods and does not try to handle every case. It therefore may
    undesirably replace user code in some cases.
    """

    if tr.type != Type.COMPONENT:
        raise ValueError(
            f"will not update code of transformation revision {tr.id}"
            f"since its type is not COMPONENT"
        )

    if not isinstance(tr.content, str):
        raise TypeError("Trafo content must be a code string for updating code.")
    existing_code = tr.content

    if existing_code == "":
        return generate_complete_component_module(tr)

    new_function_header = generate_function_header(tr)

    try:
        start, remaining = existing_code.split("# ***** DO NOT EDIT LINES BELOW *****", 1)
    except ValueError:
        # Cannot find func def, therefore append it (assuming necessary imports are present):
        # This may secretely add a second main entrypoint function!
        return existing_code + "\n\n" + new_function_header + function_body_template

    if "    # ***** DO NOT EDIT LINES ABOVE *****\n" not in remaining:
        # Cannot find end of function definition.
        # Therefore replace all code starting from the detected beginning of the function
        # definition. This deletes all user code below!
        return start + new_function_header + function_body_template

    # we now are quite sure that we find a complete existing function definition

    old_func_def, end = remaining.split("    # ***** DO NOT EDIT LINES ABOVE *****\n", 1)

    old_func_def_lines = old_func_def.split("\n")
    use_async_def = (len(old_func_def_lines) >= 3) and old_func_def_lines[-3].startswith(
        "async def"
    )
    is_coroutine = use_async_def

    new_function_header = generate_function_header(tr, is_coroutine)

    return start + new_function_header + end


def add_documentation_as_module_doc_string(code: str, tr: TransformationRevision) -> str:
    if code.startswith('"""'):
        return code

    mod_doc_string = (
        '"""Documentation for ' + tr.name + "\n\n" + tr.documentation.strip() + '\n"""\n\n'
    )

    return mod_doc_string + code


def add_test_wiring_dictionary(code: str, tr: TransformationRevision) -> str:
    try:
        expanded_code = update_module_level_variable(
            code=code,
            variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
            value=json.loads(tr.test_wiring.json(exclude_unset=True, exclude_defaults=True)),
        )
    except CodeParsingException as e:
        msg = (
            f"Failed to update test wiring in code for trafo {tr.name} ({tr.version_tag})"
            f"(id: {str(tr.id)}). Returning non-updated code. Error was: {str(e)}"
        )
        logger.warning(msg)
        return code
    return expanded_code


def add_release_wiring_dictionary(code: str, tr: TransformationRevision) -> str:
    try:
        expanded_code = update_module_level_variable(
            code=code,
            variable_name="RELEASE_WIRING",
            value=json.loads(
                tr.release_wiring.json(exclude_unset=True, exclude_defaults=True)
                if tr.release_wiring is not None
                else "null"
            ),
        )
    except CodeParsingException as e:
        msg = (
            f"Failed to update release wiring in code for trafo {tr.name} ({tr.version_tag})"
            f"(id: {str(tr.id)}). Returning non-updated code. Error was: {str(e)}"
        )
        logger.warning(msg)
        return code
    return expanded_code


def expand_code(
    tr: TransformationRevision,
) -> str:
    """Add documentation and test wiring and release wiring to component code

    Add the documentation as module docstring at the top of the component code.

    Add test_wiring as dictionary at the end of the component code.

    Add release_wiring as dictionary at the end of the component code.
    """

    if tr.type != Type.COMPONENT:
        raise ValueError(
            f"Will not update code of transformation revision {tr.id} "
            f"since its type is not COMPONENT."
        )

    existing_code = tr.content
    assert isinstance(existing_code, str)  # hint for mypy # noqa: S101

    if existing_code == "":
        existing_code = generate_complete_component_module(tr)

    expanded_code = add_documentation_as_module_doc_string(existing_code, tr)
    expanded_code = add_test_wiring_dictionary(expanded_code, tr)
    expanded_code = add_release_wiring_dictionary(expanded_code, tr)

    try:
        return format_code_with_black(expanded_code)
    except CodeParsingException:
        logger.warning(
            "Could not format code with black ({tr.name} ({tr.version_tag}), id: {tr.id})."
        )
        return expanded_code


def check_parameter_names(names: list[str]) -> bool:
    return all(name.isidentifier() and not iskeyword(name) for name in names)
