from hetdesrun.component.code import (
    generate_function_header,
    check_parameter_names,
    update_code,
    example_code,
    example_code_async,
)
from hetdesrun.datatypes import DataType


def test_function_header_no_params():
    func_header = generate_function_header(
        {},
        {}, 
        "Test Component", 
        "A test component", 
        "Tests", 
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565", 
        "1.0.0",
        "def",
    )
    assert "def main()" in func_header
    assert "inputs={}" in func_header
    assert "outputs={}" in func_header
    assert 'uuid="c6eff22c-21c4-43c6-9ae1-b2bdfb944565"' in func_header


def test_function_header_multiple_inputs():
    func_header = generate_function_header(
        {"x": DataType.Float, "okay": DataType.Boolean},
        {"output": DataType.Float},
        "Test Component",
        "A test component",
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
        "def",
    )
    assert "main(*, x, okay)" in func_header
    assert """inputs={"x": DataType.Float, "okay": DataType.Boolean}""" in func_header
    assert """outputs={"output": DataType.Float}""" in func_header
    assert 'tag="1.0.0"' in func_header


def test_check_parameter_names():
    assert check_parameter_names(["x"])
    assert not check_parameter_names(["1", "x"])


def test_update_code():
    new_code = update_code(
        example_code, 
        {}, 
        {}, 
        "Test Component", 
        "A test component", 
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.1",
    )
    assert """return {"z": x+y}""" in new_code
    assert "c6eff22c-21c4-43c6-9ae1-b2bdfb944565" in new_code
    assert "1.0.0" not in new_code

    # test with no code (new code generation)
    new_code = update_code(
        None, 
        {}, 
        {}, 
        "Test Component", 
        "A test component", 
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
    )
    assert "pass" in new_code
    assert "1.0.0" in new_code

    # test input without both start/stop markers
    new_code = update_code(
        "", 
        {}, 
        {}, 
        "Test Component", 
        "A test component", 
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
    )
    assert "pass" in new_code

    # test input without only stop marker
    new_code = update_code(
        "# ***** DO NOT EDIT LINES BELOW *****",
        {},
        {},
        "Test Component",
        "A test component",
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.0",
    )

    # test with async def in function header
    new_code = update_code(
        example_code_async, 
        {}, 
        {},
        "Test Component", 
        "A test component", 
        "Tests",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
        "1.0.1",
    )
    assert "async def" in new_code