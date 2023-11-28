"""Code template generation

This module contains functions for generating and updating component code modules
to provide a very elementary support system to the designer code editor.
"""

import re
from keyword import iskeyword

import black

from hetdesrun.datatypes import DataType
from hetdesrun.persistence.models.io import InputType, TransformationInput
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type

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
    "description": {description},
    "version_tag": {version_tag},
    "id": {id},
    "revision_group_id": {revision_group_id},
    "state": {state},{timestamp}
}}


{main_func_declaration_start} main({params_list}):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****\
"""

function_body_template: str = """\
    # write your function code here.
    pass\
"""


def wrap_in_quotes_if_data_type_string(
    default_value_string: str, data_type: DataType
) -> str:
    if data_type != DataType.String or default_value_string == "None":
        return default_value_string
    return '"' + default_value_string + '"'


def default_value_string(inp: TransformationInput) -> str:
    if inp.value == "" and inp.data_type != DataType.String:
        return "None"

    return wrap_in_quotes_if_data_type_string(str(inp.value), inp.data_type)


def generate_function_header(
    component: TransformationRevision, is_coroutine: bool = False
) -> str:
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
                inp.name + "=" + default_value_string(inp)
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
                + (
                    ', "default_value": '
                    + (
                        '"'
                        if inp.data_type == DataType.String and inp.value is not None
                        else ""
                    )
                    + (
                        str(inp.value)
                        if (inp.data_type == DataType.String or inp.value != "")
                        else "None"
                    )
                    + (
                        '"'
                        if inp.data_type == DataType.String and inp.value is not None
                        else ""
                    )
                    if inp.type == InputType.OPTIONAL
                    else ""
                )
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
                '    "'
                + output.name
                + '": {"data_type": "'
                + output.data_type.value
                + '"},\n    '
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

    return function_definition_template.format(
        input_dict_content=input_dict_str,
        output_dict_content=output_dict_str,
        name='"' + component.name + '"',
        description='"' + component.description + '"',
        category='"' + component.category + '"',
        version_tag='"' + component.version_tag + '"',
        id='"' + str(component.id) + '"',
        revision_group_id='"' + str(component.revision_group_id) + '"',
        state='"' + component.state + '"',
        timestamp=timestamp_str,
        params_list=param_list_str,
        main_func_declaration_start=main_func_declaration_start,
    )


def generate_complete_component_module(
    component: TransformationRevision, is_coroutine: bool = False
) -> str:
    return (
        imports_template
        + "\n"
        + generate_function_header(component, is_coroutine)
        + "\n"
        + function_body_template
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
        start, remaining = existing_code.split(
            "# ***** DO NOT EDIT LINES BELOW *****", 1
        )
    except ValueError:
        # Cannot find func def, therefore append it (assuming necessary imports are present):
        # This may secretely add a second main entrypoint function!
        return (
            existing_code + "\n\n" + new_function_header + "\n" + function_body_template
        )

    if "    # ***** DO NOT EDIT LINES ABOVE *****" not in remaining:
        # Cannot find end of function definition.
        # Therefore replace all code starting from the detected beginning of the function
        # definition. This deletes all user code below!
        return start + new_function_header + "\n" + function_body_template

    # we now are quite sure that we find a complete existing function definition

    old_func_def, end = remaining.split("    # ***** DO NOT EDIT LINES ABOVE *****", 1)

    old_func_def_lines = old_func_def.split("\n")
    use_async_def = (len(old_func_def_lines) >= 3) and old_func_def_lines[
        -3
    ].startswith("async def")
    is_coroutine = use_async_def

    new_function_header = generate_function_header(tr, is_coroutine)

    return start + new_function_header + end


def remove_module_doc_string(code: str) -> str:
    if code.startswith('"""') and code.count('"""') > 1:
        _, _, remaining_code = code.split('"""', 2)

        code = remaining_code.strip()

    return code


def add_documentation_as_module_doc_string(
    code: str, tr: TransformationRevision
) -> str:
    code = remove_module_doc_string(code)

    mod_doc_string = (
        '"""Documentation for '
        + tr.name
        + "\n\n"
        + tr.documentation.strip()
        + '\n"""\n\n'
    )

    return mod_doc_string + code


def remove_test_wiring_dictionary(code: str) -> str:
    if re.match(
        pattern=r".*^TEST_WIRING_FROM_PY_FILE_IMPORT",
        string=code,
        flags=re.DOTALL | re.MULTILINE,
    ):
        split_string = re.split(
            pattern=r"^TEST_WIRING_FROM_PY_FILE_IMPORT",
            string=code,
            flags=re.DOTALL | re.MULTILINE,
        )
        if len(split_string) != 2:
            raise ValueError(
                "Apparently there is more than one occurence of 'TEST_WIRING_FROM_PY_FILE_IMPORT' "
                "at the beginning of a line, resulting in the split string:\n%s",
                ".\n".join(split_string),
            )
        preceding_code, test_wiring_and_subsequent_code = split_string
        if "\n}\n" in test_wiring_and_subsequent_code:
            _, subsequent_code = test_wiring_and_subsequent_code.split("\n}\n", 1)
            code = preceding_code + "\n" + subsequent_code

    return code


def add_test_wiring_dictionary(code: str, tr: TransformationRevision) -> str:
    code = remove_test_wiring_dictionary(code)

    test_wiring_dictionary_string = (
        "\n\nTEST_WIRING_FROM_PY_FILE_IMPORT = "
        + tr.test_wiring.json(exclude_unset=True, exclude_defaults=True)
        + "\n"
    )

    return code + test_wiring_dictionary_string


def format_code_with_black(code: str) -> str:
    try:
        code = black.format_file_contents(
            code,
            fast=False,
            mode=black.Mode(
                target_versions={black.TargetVersion.PY311}, line_length=100
            ),
        )
    except black.NothingChanged:
        pass
    finally:
        # Make sure there's a newline after the content
        if len(code) != 0 and code[-1] != "\n":
            code += "\n"
    return code


def reduce_code(code: str) -> str:
    updated_code = format_code_with_black(code)
    updated_code = remove_module_doc_string(updated_code)
    updated_code = remove_test_wiring_dictionary(updated_code)
    return updated_code


def expand_code(
    tr: TransformationRevision,
) -> str:
    """Add documentation and test wiring to component code

    Add the documentation as module docstring at the top of the component code.

    Add test_wiring as dictionary at the end of the component code.
    """

    if tr.type != Type.COMPONENT:
        raise ValueError(
            f"will not update code of transformation revision {tr.id}"
            f"since its type is not COMPONENT"
        )

    if not isinstance(tr.content, str):
        raise TypeError(
            "Transformation revision %s has content that is not a string!", str(tr.id)
        )
    existing_code = tr.content

    if existing_code == "":
        existing_code = generate_complete_component_module(tr)

    existing_code = format_code_with_black(existing_code)

    return add_test_wiring_dictionary(
        add_documentation_as_module_doc_string(existing_code.strip(), tr), tr
    )


def check_parameter_names(names: list[str]) -> bool:
    return all(name.isidentifier() and not iskeyword(name) for name in names)
