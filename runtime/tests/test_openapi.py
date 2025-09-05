import json

import pytest


# Suppressing duplicate operation_id warnings due to FastAPI's route registration behavior.
# The warning occurs only here because this test requests the OpenAPI schema (/openapi.json),
# triggering duplicate operation_id validation (see https://github.com/fastapi/fastapi/issues/4740).
@pytest.mark.filterwarnings(
    "ignore:Duplicate Operation ID receive_execution_response__callback_url__post "
    "for function receive_execution_response:UserWarning"
)
def test_openapi_json_file_in_repo(app_without_auth, apply_fixes):
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
