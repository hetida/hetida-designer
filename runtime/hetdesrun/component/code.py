"""Code template generation

This module contains functions for generating and updating component code modules
to provide a very elementary support system to the designer code editor.
"""


from typing import Optional, List
from keyword import iskeyword

from hetdesrun.models.code import ComponentInfo

imports_template: str = """\
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
# add your own imports here, e.g.
#     import pandas as pd
#     import numpy as np

"""

function_definition_template: str = """\
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
@register(
    inputs={input_dict_content},
    outputs={output_dict_content},
    name={name},
    description={description},
    category={category},
    id={id},
    revision_group_id={revision_group_id},
    version_tag={version_tag}
)
{main_func_declaration_start} main({params_list}):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****\
"""

function_body_template: str = """\
    # write your function code here.
    pass\
"""


def generate_function_header(component_info: ComponentInfo) -> str:
    """Generate entrypoint function header from the inputs and their types"""
    param_list_str = (
        ""
        if len(component_info.input_types_by_name.keys()) == 0
        else "*, " + ", ".join(component_info.input_types_by_name.keys())
    )

    main_func_declaration_start = "async def" if component_info.is_coroutine else "def"

    return function_definition_template.format(
        input_dict_content="{"
        + ", ".join(
            [
                '"' + key + '": DataType.' + value.name
                for key, value in component_info.input_types_by_name.items()
            ]
        )
        + "}",
        output_dict_content="{"
        + ", ".join(
            [
                '"' + key + '": DataType.' + value.name
                for key, value in component_info.output_types_by_name.items()
            ]
        )
        + "}",
        name='"' + component_info.name + '"',
        description='"' + component_info.description + '"',
        category='"' + component_info.category + '"',
        id='"' + str(component_info.id) + '"',
        revision_group_id='"' + str(component_info.revision_group_id) + '"',
        version_tag='"' + component_info.version_tag + '"',
        params_list=param_list_str,
        main_func_declaration_start=main_func_declaration_start,
    )


def generate_complete_component_module(component_info: ComponentInfo) -> str:
    return (
        imports_template
        + "\n"
        + generate_function_header(component_info)
        + "\n"
        + function_body_template
    )


def update_code(
    existing_code: Optional[str],
    component_info: ComponentInfo,
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
    if existing_code is None or existing_code == "":
        return generate_complete_component_module(component_info)

    new_function_header = generate_function_header(component_info)

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
    component_info.is_coroutine = use_async_def

    new_function_header = generate_function_header(component_info)

    return start + new_function_header + end


def check_parameter_names(names: List[str]) -> bool:
    return all((name.isidentifier() and not iskeyword(name) for name in names))
