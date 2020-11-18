import pytest
from hetdesrun.component.load import import_func_from_code_with_uuid_as_modulename


def test_importing():
    with pytest.raises(ImportError):

        import_func_from_code_with_uuid_as_modulename(
            """def main():\n    pass""",
            "my_module_1234",
            "main",
            raise_if_not_found=True,
        )

    # this time it should be actually imported
    import_func_from_code_with_uuid_as_modulename(
        """def main():\n    pass""", "my_module_1234", "main"
    )

    # do it again, since from now on the module is loaded from memory and not from the code
    # (goes through different lines in the function)
    import_func_from_code_with_uuid_as_modulename(
        """def main():\n    pass""", "my_module_1234", "main", raise_if_not_found=True
    )
