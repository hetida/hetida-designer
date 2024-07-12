import json
import os
import subprocess

import pytest

from hetdesrun.component.code import (
    add_documentation_as_module_doc_string,
    add_test_wiring_dictionary,
    check_parameter_names,
    expand_code,
    generate_function_header,
    update_code,
)
from hetdesrun.datatypes import DataType
from hetdesrun.models.code import example_code, example_code_async
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    TransformationInput,
    TransformationOutput,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_json, load_python_file


def test_function_header_no_params():
    component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert (
        func_header
        == """\
# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {},
    "outputs": {},
    "name": "Test Component",
    "category": "Tests",
    "description": "A test component",
    "version_tag": "1.0.0",
    "id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "revision_group_id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main():
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
"""
    )


def test_function_header_description_line_too_long():
    component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description=(
            "A very long test component description so that the line is longer than allowed"
        ),
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert "# noqa: E501" in func_header


def test_function_header_multiple_inputs():
    component = TransformationRevision(
        io_interface=IOInterface(
            inputs=[
                TransformationInput(name="x", data_type=DataType.Float),
                TransformationInput(name="okay", data_type=DataType.Boolean),
            ],
            outputs=[TransformationOutput(name="output", data_type=DataType.Float)],
        ),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert "main(*, x, okay)" in func_header
    assert (
        """
    "inputs": {
        "x": {"data_type": "FLOAT"},
        "okay": {"data_type": "BOOLEAN"},
    },
    """
        in func_header
    )
    assert (
        """
    "outputs": {
        "output": {"data_type": "FLOAT"},
    },
    """
        in func_header
    )
    assert '"version_tag": "1.0.0"' in func_header


def test_function_header_optional_inputs():
    component = TransformationRevision(
        io_interface=IOInterface(
            inputs=[
                TransformationInput(
                    name="x",
                    data_type=DataType.Float,
                    type=InputType.OPTIONAL,
                    value="1.2",
                ),
                TransformationInput(
                    name="okay",
                    data_type=DataType.Boolean,
                    type=InputType.OPTIONAL,
                    value="false",
                ),
                TransformationInput(
                    name="neither_nor_ok",
                    data_type=DataType.Boolean,
                    type=InputType.OPTIONAL,
                    value="",
                ),
                TransformationInput(
                    name="text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                    value="text",
                ),
                TransformationInput(
                    name="no_text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                ),
                TransformationInput(
                    name="empty_text",
                    data_type=DataType.String,
                    type=InputType.OPTIONAL,
                    value="",
                ),
                TransformationInput(
                    name="no_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                ),
                TransformationInput(
                    name="null_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                    value="null",
                ),
                TransformationInput(
                    name="empty_string_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                    value="",
                ),
                TransformationInput(
                    name="some_string_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                    value="any",
                ),
                TransformationInput(
                    name="some_number_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                    value="23",
                ),
                TransformationInput(
                    name="some_json_any",
                    data_type=DataType.Any,
                    type=InputType.OPTIONAL,
                    value='{"test": true, "content": null, "sub_structure": {"relevant": false}}',
                ),
                TransformationInput(
                    name="series",
                    data_type=DataType.Series,
                    type=InputType.OPTIONAL,
                    value=(
                        '{"2020-01-01T01:15:27.000Z": 42.2, "2020-01-03T08:20:03.000Z": 18.7, '
                        '"2020-01-03T08:20:04.000Z": 25.9}'
                    ),
                ),
            ],
            outputs=[TransformationOutput(name="output", data_type=DataType.Float)],
        ),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    func_header = generate_function_header(component)
    assert '"default_value": False' in func_header
    assert '"default_value": None' in func_header
    assert '"default_value": 1.2' in func_header
    assert '"default_value": "text"' in func_header
    assert '"default_value": "None"' not in func_header
    assert '"default_value": ""' in func_header
    assert '"default_value": "any"' in func_header
    assert '"default_value": 23' in func_header
    assert (
        '"default_value": {\n'
        '                "test": True,\n'
        '                "content": None,\n'
        '                "sub_structure": {"relevant": False},\n'
        "            }" in func_header
    )
    assert (
        "def main(\n"
        "    *,\n"
        "    x=1.2,\n"
        "    okay=False,\n"
        "    neither_nor_ok=None,\n"
        '    text="text",\n'
        "    no_text=None,\n"
        '    empty_text="",\n'
        '    no_any=parse_default_value(COMPONENT_INFO, "no_any"),\n'
        '    null_any=parse_default_value(COMPONENT_INFO, "null_any"),\n'
        '    empty_string_any=parse_default_value(COMPONENT_INFO, "empty_string_any"),\n'
        '    some_string_any=parse_default_value(COMPONENT_INFO, "some_string_any"),\n'
        '    some_number_any=parse_default_value(COMPONENT_INFO, "some_number_any"),\n'
        '    some_json_any=parse_default_value(COMPONENT_INFO, "some_json_any"),\n'
        '    series=parse_default_value(COMPONENT_INFO, "series"),\n'
        "):"
    ) in func_header

    component_with_none = TransformationRevision(
        io_interface=IOInterface(
            inputs=[
                TransformationInput(
                    name="none",
                    data_type=DataType.Float,
                    type=InputType.OPTIONAL,
                    value="None",
                ),
            ],
            outputs=[TransformationOutput(name="output", data_type=DataType.Float)],
        ),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="DRAFT",
        type="COMPONENT",
        content="",
        test_wiring=[],
    )
    with pytest.raises(
        TypeError,
        match="Parsing Error for value 'None' of input 'none' as FLOAT. Enter 'null' instead.",
    ):
        generate_function_header(component_with_none)


def test_check_parameter_names():
    assert check_parameter_names(["x"])
    assert not check_parameter_names(["1", "x"])


def test_update_code_without_io():
    component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.0",
        state="RELEASED",
        type="COMPONENT",
        released_timestamp="2019-12-01T12:00:00+00:00",
        content=example_code,
        test_wiring=[],
    )
    updated_component = TransformationRevision(
        io_interface=IOInterface(inputs=[], outputs=[]),
        name="Test Component",
        description="A test component",
        category="Tests",
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        version_tag="1.0.1",
        state="DRAFT",
        type="COMPONENT",
        content=example_code,
        test_wiring=[],
    )
    new_code = update_code(updated_component)
    assert """return {"z": x+y}""" in new_code
    assert "c6eff22c-21c4-43c6-9ae1-b2bdfb944565" in new_code
    assert "1.0.0" not in new_code

    # test input without both start/stop markers
    component.content = ""
    new_code = update_code(component)
    assert "pass" in new_code

    # test input without only stop marker
    component.content = "# ***** DO NOT EDIT LINES BELOW *****"
    new_code = update_code(component)
    assert "pass" in new_code

    # test with async def in function header
    component.content = example_code_async
    new_code = update_code(component)
    assert "async def" in new_code


def test_update_code_with_optional_inputs():
    json_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_optional_inputs_component.json",
    )
    with open(json_path) as f:
        tr_json = json.load(f)

    tr = TransformationRevision(**tr_json)

    updated_code = update_code(tr)

    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_optional_inputs_component.py",
    )
    with open(py_path) as f:
        code_from_file = f.read()

    assert updated_code == code_from_file


def test_add_documentation_as_module_docstring():
    component_tr_path = "tests/data/components/reduced_code.json"
    component_tr = TransformationRevision(**load_json(component_tr_path))
    assert "test" not in component_tr.content

    component_tr.documentation = "test"
    code_with_updated_module_doc_string = add_documentation_as_module_doc_string(
        component_tr.content, component_tr
    )
    assert 'test\n"""' in code_with_updated_module_doc_string

    component_tr.documentation = "test\n"
    code_with_updated_module_doc_string = add_documentation_as_module_doc_string(
        component_tr.content, component_tr
    )
    assert 'test\n"""' in code_with_updated_module_doc_string


def test_add_test_wiring_dictionary():
    component_tr_path = "tests/data/components/reduced_code.json"
    component_tr = TransformationRevision(**load_json(component_tr_path))
    component_code_path = "tests/data/components/reduced_code.py"
    component_code_without_test_wiring_dictionary = load_python_file(component_code_path)

    assert "TEST_WIRING_FROM_PY_FILE_IMPORT" not in component_code_without_test_wiring_dictionary
    component_code_with_new_test_wiring_dictionary = add_test_wiring_dictionary(
        component_code_without_test_wiring_dictionary, component_tr
    )
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT" in component_code_with_new_test_wiring_dictionary

    assert "24" not in component_code_without_test_wiring_dictionary
    component_tr.test_wiring.input_wirings[1].filters["value"] = "24"
    component_code_with_updated_test_wiring_dictionary = add_test_wiring_dictionary(
        component_code_without_test_wiring_dictionary, component_tr
    )
    assert "24" in component_code_with_updated_test_wiring_dictionary


def test_expand_code():
    reduced_component_tr_path = "tests/data/components/reduced_code.json"
    reduced_component_tr = TransformationRevision(**load_json(reduced_component_tr_path))

    expanded_component_code_path = "tests/data/components/expanded_code.py"
    expanded_component_code = load_python_file(expanded_component_code_path)

    expanded_reduced_code = expand_code(reduced_component_tr)
    assert expanded_reduced_code != reduced_component_tr.content
    assert expanded_reduced_code == expanded_component_code


def test_hdctl_contains_correct_hdutils_py_file():
    """hdctls version of hdutils should always be identica

    This checks whether the version of hdutils.py included inside hdctl
    agrees with the one in this repository.

    hdctl includes this file to be easily distributable as a single bash script
    file. It needs it to create hdutils.py file for example when syncing to make
    components as py files runnable directly.
    """
    with open("hdutils.py", "r") as f:  # noqa: UP015
        hdutils_py_content = f.read()
    hdctl_output = subprocess.check_output(
        ["bash", "../hdctl", "_output_hdutils_py_content"]  # noqa: S607,S603
    ).decode("utf-8")

    assert hdctl_output.strip() == hdutils_py_content.strip()
