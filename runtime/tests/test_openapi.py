import json


def test_openapi_json(app_without_auth, apply_fixes):
    """Ensures that the openapi.json in this repo is up to date

    This test can update the openapi.json file automatically if
    pytest is run with --apply-fixes
    """
    openapi_dictlike = app_without_auth.openapi()
    openapi_expected_file_content_str = json.dumps(openapi_dictlike, indent=2)

    try:
        with open("openapi.json") as f:
            file_content = f.read()
    except FileNotFoundError:
        file_content = ""

    if openapi_expected_file_content_str != file_content and apply_fixes:
        with open("openapi.json", "w") as f:
            f.write(openapi_expected_file_content_str)

    try:
        with open("openapi.json") as f:
            file_content = f.read()
    except FileNotFoundError:
        file_content = ""

    assert openapi_expected_file_content_str == file_content
