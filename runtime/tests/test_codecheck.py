from hetdesrun.component.load import check_importability


def test_importability_check():
    test_code = """def main():\n    pass"""  # correct code
    assert check_importability(test_code, "main")[0]

    test_code = """def main()\n    pass"""  # syntax error (missing colon)
    assert not check_importability(test_code, "main")[0]

    test_code = """def maaain():\n    pass"""  # function to import does not exist
    assert not check_importability(test_code, "main")[0]
