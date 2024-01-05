import pytest

from hetdesrun.component.code_utils import CodeParsingException, format_code_with_black
from hetdesrun.trafoutils.io.load import load_python_file


def test_format_code_with_black():
    component_code_path = "tests/data/components/reduced_code.py"
    component_code = load_python_file(component_code_path)
    unformatted_component_code = component_code.replace(" = ", "=")
    assert unformatted_component_code != component_code

    formatted_code = format_code_with_black(unformatted_component_code)
    assert formatted_code != unformatted_component_code
    assert formatted_code == component_code


def test_format_code_with_syntax_error_with_black():
    component_code_path = "tests/data/components/reduced_code.py"
    component_code = load_python_file(component_code_path)
    component_code_with_syntax_error = component_code.replace("):", ")")
    assert component_code_with_syntax_error != component_code

    with pytest.raises(CodeParsingException):
        format_code_with_black(component_code_with_syntax_error)
