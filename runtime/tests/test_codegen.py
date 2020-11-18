from hetdesrun.component.code import (
    generate_function_header,
    check_parameter_names,
    update_code,
    example_code,
)
from hetdesrun.datatypes import DataType


def test_function_header_no_params():
    func_header = generate_function_header({}, {})
    assert "main()" in func_header
    assert "inputs={}" in func_header
    assert "outputs={}" in func_header


def test_function_header_multiple_inputs():
    func_header = generate_function_header(
        {"x": DataType.Float, "okay": DataType.Boolean}, {"output": DataType.Float}
    )
    assert "main(*, x, okay)" in func_header
    assert """inputs={"x": DataType.Float, "okay": DataType.Boolean}""" in func_header
    assert """outputs={"output": DataType.Float}""" in func_header


def test_check_parameter_names():
    assert check_parameter_names(["x"])
    assert not check_parameter_names(["1", "x"])


def test_update_code():
    func_body = """return {"z":x + y}"""
    test_code = example_code.replace("pass", func_body)
    new_code = update_code(test_code, {}, {})
    assert func_body in new_code
    assert "pass" not in new_code

    # test with no code (new code generation)
    new_code = update_code(None, {}, {})
    assert "pass" in new_code

    # test input without both start/stop markers
    new_code = update_code(" ", {}, {})
    assert "pass" in new_code

    # test input without only stop marker
    new_code = update_code("# ***** DO NOT EDIT LINES BELOW *****", {}, {})
    assert "pass" in new_code
