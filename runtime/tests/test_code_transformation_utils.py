import pytest

from hetdesrun.component.code_utils import (
    CodeParsingException,
    format_code_with_black,
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


def test_format_code_with_black(reduced_component_code: str):
    unformatted_component_code = reduced_component_code.replace(" = ", "=")
    assert unformatted_component_code != reduced_component_code

    formatted_code = format_code_with_black(unformatted_component_code)
    assert formatted_code != unformatted_component_code
    assert formatted_code == reduced_component_code


def test_format_code_with_syntax_error_with_black(reduced_component_code: str):
    component_code_with_syntax_error = reduced_component_code.replace("):", ")")
    assert component_code_with_syntax_error != reduced_component_code

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


def test_add_module_level_variable(reduced_component_code: str):
    updated_code = update_module_level_variable(
        code=reduced_component_code, variable_name="TEST", value=None
    )

    assert "TEST = None" in updated_code


def test_update_module_level_variable(reduced_component_code: str):
    updated_code = update_module_level_variable(
        code=reduced_component_code,
        variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
        value={"input_wirings": []},
    )

    assert '"adapter_id": "direct_provisioning"' not in updated_code
    assert 'TEST_WIRING_FROM_PY_FILE_IMPORT = {"input_wirings": []}\n' in updated_code


def test_update_module_level_variable_in_code_with_syntax_error(
    expanded_component_code: str,
):
    component_code_with_syntax_error = expanded_component_code.replace("):", ")")
    assert component_code_with_syntax_error != expanded_component_code

    with pytest.raises(CodeParsingException):
        update_module_level_variable(
            code=component_code_with_syntax_error,
            variable_name="TEST_WIRING_FROM_PY_FILE_IMPORT",
            value={"input_wirings": []},
        )
