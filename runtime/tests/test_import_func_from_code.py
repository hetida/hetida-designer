import pytest

from hetdesrun.component.load import ComponentCodeImportError, import_func_from_code


def test_importing_valid_code():
    func_name = "main"
    valid_code = """def main():\n    pass"""

    with pytest.raises(ImportError):
        import_func_from_code(
            valid_code,
            func_name,
            raise_if_not_found=True,
            register_module=True,
        )

    # this time it should be actually imported
    import_func_from_code(
        valid_code,
        func_name,
    )

    # do it again, since from now on the module is loaded from memory and not from the code
    # (goes through different lines in the function)
    import_func_from_code(
        valid_code,
        func_name,
        raise_if_not_found=True,
        register_module=True,
    )


def test_importing_code_with_wrong_import():
    func_name = "main"
    invalid_code = """import nonexistingmodule; def main():\n    pass"""

    with pytest.raises(ComponentCodeImportError):
        import_func_from_code(
            invalid_code,
            func_name,
        )

    # function with error is not registered and thus not found in 2nd import
    with pytest.raises(ImportError):
        import_func_from_code(
            invalid_code,
            func_name,
            raise_if_not_found=True,
            register_module=True,
        )
