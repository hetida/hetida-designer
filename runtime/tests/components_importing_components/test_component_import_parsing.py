from hetdesrun.component.code_utils import get_global_component_imports


def test_component_import_extraction():
    code_str = """my_comp = import_comp("caf158f6-5545-44fe-8f12-9438a6a992de")"""

    found_component_imports = get_global_component_imports(code_str)
    assert len(found_component_imports) == 1
    assert found_component_imports[0] == "caf158f6-5545-44fe-8f12-9438a6a992de"

    code_str = """
my_comp = import_comp("caf158f6-5545-44fe-8f12-9438a6a992de")
my_comp2 = import_comp("a6e4bb9b-6b85-47b2-bcb2-691b0c0ed744")
    """

    found_component_imports = get_global_component_imports(code_str)
    assert len(found_component_imports) == 2
    assert found_component_imports[0] == "caf158f6-5545-44fe-8f12-9438a6a992de"
    assert found_component_imports[1] == "a6e4bb9b-6b85-47b2-bcb2-691b0c0ed744"

    found_component_imports = get_global_component_imports("")
    assert len(found_component_imports) == 0

    # must be global:
    code_str = """
def some_func():
    my_comp = import_comp("caf158f6-5545-44fe-8f12-9438a6a992de")
    my_comp2 = import_comp("a6e4bb9b-6b85-47b2-bcb2-691b0c0ed744")
    """
    found_component_imports = get_global_component_imports(code_str)
    assert len(found_component_imports) == 0
