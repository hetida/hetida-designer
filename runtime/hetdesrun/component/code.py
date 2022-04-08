"""Code template generation

This module contains functions for generating and updating component code modules
to provide a very elementary support system to the designer code editor.
"""


from typing import Dict, Optional, List
from keyword import iskeyword
import re

from hetdesrun.datatypes import DataType


ALLOWED_CHARS_REGEXP = re.compile(
    r"[^a-zA-Z0-9\.\,\-#_ ]"  # pylint: disable=anomalous-backslash-in-string
)  # allow only some special characters for category, description and component name

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
    component_name={component_name},
    description={description},
    category={category},
    uuid={uuid},
    group_id={group_id},
    tag={tag}
)
{main_func_declaration_start} main({params_list}):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****\
"""

function_body_template: str = """\
    # write your function code here.
    pass\
"""


def sanitize(text: str) -> str:
    return re.sub(ALLOWED_CHARS_REGEXP, "", text)


def generate_function_header(
    input_type_dict: Dict[str, DataType],
    output_type_dict: Dict[str, DataType],
    component_name: str,
    description: str,
    category: str,
    uuid: str,
    group_id: str,
    tag: str,
    is_coroutine: bool = False,
) -> str:
    """Generate entrypoint function header from the inputs and their types"""
    param_list_str = (
        ""
        if len(input_type_dict.keys()) == 0
        else "*, " + ", ".join(input_type_dict.keys())
    )

    main_func_declaration_start = "async def" if is_coroutine else "def"

    return function_definition_template.format(
        input_dict_content="{"
        + ", ".join(
            [
                '"' + key + '": DataType.' + value.name
                for key, value in input_type_dict.items()
            ]
        )
        + "}",
        output_dict_content="{"
        + ", ".join(
            [
                '"' + key + '": DataType.' + value.name
                for key, value in output_type_dict.items()
            ]
        )
        + "}",
        component_name='"' + sanitize(component_name) + '"',
        description='"' + sanitize(description) + '"',
        category='"' + sanitize(category) + '"',
        uuid='"' + sanitize(uuid) + '"',
        group_id='"' + sanitize(group_id) + '"',
        tag='"' + sanitize(tag) + '"',
        params_list=param_list_str,
        main_func_declaration_start=main_func_declaration_start,
    )


def generate_complete_component_module(
    input_type_dict: Dict[str, DataType],
    output_type_dict: Dict[str, DataType],
    component_name: str,
    description: str,
    category: str,
    uuid: str,
    group_id: str,
    tag: str,
    is_coroutine: bool = False,
) -> str:
    return (
        imports_template
        + "\n"
        + generate_function_header(
            input_type_dict,
            output_type_dict,
            component_name,
            description,
            category,
            uuid,
            group_id,
            tag,
            is_coroutine,
        )
        + "\n"
        + function_body_template
    )


def update_code(
    existing_code: Optional[str],
    input_type_dict: Dict[str, DataType],
    output_type_dict: Dict[str, DataType],
    component_name: str,
    description: str,
    category: str,
    uuid: str,
    group_id: str,
    tag: str,
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
        return generate_complete_component_module(
            input_type_dict,
            output_type_dict,
            component_name=component_name,
            description=description,
            category=category,
            uuid=uuid,
            group_id=group_id,
            tag=tag,
            is_coroutine=False,
        )

    try:
        start, remaining = existing_code.split(
            "# ***** DO NOT EDIT LINES BELOW *****", 1
        )
    except ValueError:
        # Cannot find func def, therefore append it (assuming necessary imports are present):
        # This may secretely add a second main entrypoint function!
        new_function_header = generate_function_header(
            input_type_dict,
            output_type_dict,
            component_name=component_name,
            description=description,
            category=category,
            uuid=uuid,
            group_id=group_id,
            tag=tag,
            is_coroutine=False,
        )
        return (
            existing_code + "\n\n" + new_function_header + "\n" + function_body_template
        )

    if "    # ***** DO NOT EDIT LINES ABOVE *****" not in remaining:
        # Cannot find end of function definition.
        # Therefore replace all code starting from the detected beginning of the function
        # definition. This deletes all user code below!
        new_function_header = generate_function_header(
            input_type_dict,
            output_type_dict,
            component_name=component_name,
            description=description,
            category=category,
            uuid=uuid,
            group_id=group_id,
            tag=tag,
            is_coroutine=False,
        )
        return start + new_function_header + "\n" + function_body_template

    # we now are quite sure that we find a complete existing function definition

    # pylint: disable=unused-variable
    old_func_def, end = remaining.split("    # ***** DO NOT EDIT LINES ABOVE *****", 1)

    old_func_def_lines = old_func_def.split("\n")
    use_async_def = (len(old_func_def_lines) >= 3) and old_func_def_lines[
        -3
    ].startswith("async def")

    new_function_header = generate_function_header(
        input_type_dict,
        output_type_dict,
        component_name=component_name,
        description=description,
        category=category,
        uuid=uuid,
        group_id=group_id,
        tag=tag,
        is_coroutine=use_async_def,
    )

    return start + new_function_header + end


example_code = (
    generate_complete_component_module(
        {"x": DataType.Float, "y": DataType.Float},
        {"z": DataType.Float},
        "Example Component",
        "An example for code generation",
        "Examples",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
        False,
    )
    + """\n    return {"z": x+y}"""
)

example_code_async = (
    generate_complete_component_module(
        {"x": DataType.Float, "y": DataType.Float},
        {"z": DataType.Float},
        "Example Component",
        "An example for code generation",
        "Examples",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
        True,
    )
    + """\n    return {"z": x+y}"""
)


def check_parameter_names(names: List[str]) -> bool:
    return all((name.isidentifier() and not iskeyword(name) for name in names))
