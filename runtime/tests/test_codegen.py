from hetdesrun.component.code import (
    generate_function_header,
    check_parameter_names,
    update_code,
)
from hetdesrun.models.code import ComponentInfo, example_code, example_code_async
from hetdesrun.datatypes import DataType


def test_function_header_no_params():
    component_info = ComponentInfo(
        input_types_by_name={},
        output_types_by_name={}, 
        name="Test Component", 
        description="A test component", 
        category="Tests", 
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        version_tag="1.0.0",
        state="DRAFT",
    )
    func_header = generate_function_header(component_info)
    assert "main()" in func_header
    assert '"inputs": {' in func_header
    assert '"outputs": {' in func_header
    assert '"id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565"' in func_header


def test_function_header_multiple_inputs():
    component_info = ComponentInfo(
        input_types_by_name={"x": DataType.Float, "okay": DataType.Boolean},
        output_types_by_name={"output": DataType.Float}, 
        name="Test Component", 
        description="A test component", 
        category="Tests", 
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        version_tag="1.0.0",
        state="DRAFT",
    )
    func_header = generate_function_header(component_info)
    assert "main(*, x, okay)" in func_header
    assert """
    "inputs": {
        "x": "FLOAT",
        "okay": "BOOLEAN",
    },
    """ in func_header
    assert """
    "outputs": {
        "output": "FLOAT",
    },
    """ in func_header
    assert '"version_tag": "1.0.0"' in func_header


def test_check_parameter_names():
    assert check_parameter_names(["x"])
    assert not check_parameter_names(["1", "x"])


def test_update_code():
    component_info = ComponentInfo(
        input_types_by_name={},
        output_types_by_name={}, 
        name="Test Component", 
        description="A test component", 
        category="Tests", 
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        version_tag="1.0.0",
        state="RELEASED",
    )
    updated_component_info = ComponentInfo(
        input_types_by_name={},
        output_types_by_name={}, 
        name="Test Component", 
        description="A test component", 
        category="Tests", 
        id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        revision_group_id="c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        version_tag="1.0.1",
        state="DRAFT",
    )
    new_code = update_code(
        example_code, 
        updated_component_info,
    )
    assert """return {"z": x+y}""" in new_code
    assert "c6eff22c-21c4-43c6-9ae1-b2bdfb944565" in new_code
    assert "1.0.0" not in new_code

    # test with no code (new code generation)
    new_code = update_code(
        None, 
        component_info,
    )
    assert "pass" in new_code
    assert "1.0.0" in new_code

    # test input without both start/stop markers
    new_code = update_code(
        "", 
        component_info,
    )
    assert "pass" in new_code

    # test input without only stop marker
    new_code = update_code(
        "# ***** DO NOT EDIT LINES BELOW *****",
        component_info,
    )

    # test with async def in function header
    new_code = update_code(
        example_code_async, 
        component_info,
    )
    assert "async def" in new_code
