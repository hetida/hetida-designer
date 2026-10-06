import json
from collections.abc import Generator
from unittest import mock

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from hetdesrun.webservice.application import init_app


@pytest.fixture()
def app_without_auth_with_all_optional_routers(deactivate_auth: Generator) -> FastAPI:
    """App with routers which are deactivated by default mounted

    The openapi.json should document all endpoints which can be activated via configuration,
    not only the ones available with default configuration.
    """
    with (
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.maintenance_secret",
            SecretStr("openapisecret"),
        ),
        mock.patch(
            "hetdesrun.adapters.blob_storage.config.blob_storage_adapter_config"
            ".adapter_hierarchy_location",
            "tests/data/blob_storage/blob_storage_adapter_hierarchy.json",
        ),
    ):
        return init_app()


# Suppressing duplicate operation_id warnings due to FastAPI's route registration behavior.
# The warning occurs only here because this test requests the OpenAPI schema (/openapi.json),
# triggering duplicate operation_id validation (see https://github.com/fastapi/fastapi/issues/4740).
@pytest.mark.filterwarnings(
    "ignore:Duplicate Operation ID receive_execution_response__callback_url__post "
    "for function receive_execution_response:UserWarning"
)
def test_openapi_json_file_in_repo(app_without_auth_with_all_optional_routers, apply_fixes):
    """Ensures that the openapi.json in this repo is up to date

    This test can update the openapi.json file automatically if
    pytest is run with --apply-fixes
    """
    openapi_dictlike = app_without_auth_with_all_optional_routers.openapi()
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
