import pytest

from hetdesrun.component.code_utils import (
    CodeParsingException,
    format_code_with_black,
    get_global_from_code,
    get_module_doc_string,
    update_module_level_variable,
)
from hetdesrun.trafoutils.io.load import load_python_file


@pytest.fixture()
def expanded_component_code() -> str:
    component_code_path = "tests/data/components/expanded_code.py"
    return load_python_file(component_code_path)


@pytest.fixture()
def reduced_component_code() -> str:
    component_code_path = "tests/data/components/reduced_code.py"
    return load_python_file(component_code_path)


@pytest.fixture()
def component_code_with_syntax_error(reduced_component_code: str) -> str:
    return reduced_component_code.replace("):", ")")


def test_format_code_with_black(reduced_component_code: str):
    unformatted_component_code = reduced_component_code.replace(" = ", "=")
    assert unformatted_component_code != reduced_component_code

    formatted_code = format_code_with_black(unformatted_component_code)
    assert formatted_code != unformatted_component_code
    assert formatted_code == reduced_component_code

    # no error raised when nothing changed
    format_code_with_black(formatted_code)


def test_format_code_with_syntax_error_with_black(
    component_code_with_syntax_error: str,
):
    with pytest.raises(CodeParsingException):
        format_code_with_black(component_code_with_syntax_error)


def test_get_module_doc_string_from_code_without_doc_string(
    reduced_component_code: str,
):
    doc_string = get_module_doc_string(reduced_component_code)

    assert doc_string is None


def test_get_module_doc_string_from_code_with_doc_string(expanded_component_code: str):
    doc_string = get_module_doc_string(expanded_component_code)

    assert doc_string is not None
    assert doc_string.startswith("Documentation for Alerts from Score")


def test_get_global_from_code_with_it(expanded_component_code: str):
    value_of_gobal = get_global_from_code(
        expanded_component_code, "TEST_WIRING_FROM_PY_FILE_IMPORT"
    )
    assert isinstance(value_of_gobal, dict)
    assert "input_wirings" in value_of_gobal
    assert len(value_of_gobal["input_wirings"]) == 2
    assert value_of_gobal["input_wirings"][0]["workflow_input_name"] == "scores"


def test_get_global_from_code_without_it(reduced_component_code: str):
    value_of_gobal = get_global_from_code(reduced_component_code, "TEST_WIRING_FROM_PY_FILE_IMPORT")
    assert value_of_gobal is None


def test_get_global_from_code_with_invalid_syntax(
    component_code_with_syntax_error: str,
):
    with pytest.raises(CodeParsingException):
        get_global_from_code(component_code_with_syntax_error, "TEST_WIRING_FROM_PY_FILE_IMPORT")


def test_add_module_level_variable(reduced_component_code: str):
    updated_code = update_module_level_variable(
        code=reduced_component_code, variable_name="TEST", value=None
    )

    assert "TEST = None" in updated_code


def test_update_module_level_variable(expanded_component_code: str):
    assert '"workflow_input_name": "scores"' in expanded_component_code

    updated_code = update_module_level_variable(
        code=expanded_component_code,
        variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
        value={"input_wirings": []},
    )

    assert '"workflow_input_name": "scores"' not in updated_code
    assert 'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n' in updated_code


def test_update_one_of_two_module_level_variable_assignments(
    expanded_component_code: str,
):
    second_test_wiring = """TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n"""
    expanded_component_code_with_second_test_wiring = expanded_component_code + second_test_wiring
    assert '"workflow_input_name": "scores"' in expanded_component_code_with_second_test_wiring
    assert (
        'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n'
        in expanded_component_code_with_second_test_wiring
    )

    updated_code = update_module_level_variable(
        code=expanded_component_code_with_second_test_wiring,
        variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
        value={},
    )

    assert '"workflow_input_name": "scores"' not in updated_code
    assert 'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n' not in updated_code
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT = {" + "}\n" in updated_code


def test_update_module_level_variable_with_same_variable_in_function_scope(
    expanded_component_code: str,
):
    second_test_wiring = """TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n"""
    expanded_component_code_with_second_test_wiring_in_function_scope = (
        expanded_component_code.replace(
            'alerts.name = "alerts"',
            'alerts.name = "alerts"\n    ' + second_test_wiring,
        )
    )
    assert (
        '"workflow_input_name": "scores"'
        in expanded_component_code_with_second_test_wiring_in_function_scope
    )
    assert (
        'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n'
        in expanded_component_code_with_second_test_wiring_in_function_scope
    )

    updated_code = update_module_level_variable(
        code=expanded_component_code_with_second_test_wiring_in_function_scope,
        variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
        value={},
    )

    assert '"workflow_input_name": "scores"' not in updated_code
    assert 'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n' in updated_code
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT = {" + "}\n" in updated_code


def test_update_module_level_variable_in_code_with_syntax_error(
    component_code_with_syntax_error: str,
):
    with pytest.raises(CodeParsingException, match="Failure parsing code"):
        update_module_level_variable(
            code=component_code_with_syntax_error,
            variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
            value={"input_wirings": []},
        )


def test_update_module_level_variable_with_unsuitable_value(
    expanded_component_code: str,
):
    with pytest.raises(CodeParsingException, match="Failure updating code"):
        update_module_level_variable(
            code=expanded_component_code,
            variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
            value=str,
        )
