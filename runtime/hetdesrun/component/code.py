"""Code template generation

This module contains functions for generating and updating component code modules
to provide a very elementary support system to the designer code editor.
"""

from keyword import iskeyword
from typing import List

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


def generate_function_header(
    component: TransformationRevision, is_coroutine: bool = False
) -> str:
    """Generate entrypoint function header from the inputs and their types"""
    param_list_str = (
        ""
        if len(component.io_interface.inputs) == 0
        else "*, "
        + ", ".join(
            input.name
            for input in component.io_interface.inputs
            if input.name is not None
        )
    )

    main_func_declaration_start = "async def" if is_coroutine else "def"

    input_dict_str = (
        "{"
        + ("\n    " if len(component.io_interface.inputs) != 0 else "")
        + "".join(
            [
                '    "' + input.name + '": "' + input.data_type.value + '",\n    '
                for input in component.io_interface.inputs
                if input.name is not None
            ]
        )
        + "}"
    )

    output_dict_str = (
        "{"
        + ("\n    " if len(component.io_interface.outputs) != 0 else "")
        + "".join(
            [
                '    "' + output.name + '": "' + output.data_type.value + '",\n    '
                for output in component.io_interface.outputs
                if output.name is not None
            ]
        )
        + "}"
    )

    timestamp_str = ""

    if component.state == State.RELEASED:
        assert component.released_timestamp is not None
        timestamp_str = "\n    " + '"released_timestamp": "'
        timestamp_str = timestamp_str + component.released_timestamp.isoformat()
        timestamp_str = timestamp_str + '",'

    if component.state == State.DISABLED:
        assert component.released_timestamp is not None
        timestamp_str = "\n    " + '"released_timestamp": "'
        timestamp_str = timestamp_str + component.released_timestamp.isoformat()
        timestamp_str = timestamp_str + '",'
        assert component.disabled_timestamp is not None
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
    assert isinstance(tr.content, str)
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

    # pylint: disable=unused-variable
    old_func_def, end = remaining.split("    # ***** DO NOT EDIT LINES ABOVE *****", 1)

    old_func_def_lines = old_func_def.split("\n")
    use_async_def = (len(old_func_def_lines) >= 3) and old_func_def_lines[
        -3
    ].startswith("async def")
    is_coroutine = use_async_def

    new_function_header = generate_function_header(tr, is_coroutine)

    return start + new_function_header + end


def check_parameter_names(names: List[str]) -> bool:
    return all((name.isidentifier() and not iskeyword(name) for name in names))
