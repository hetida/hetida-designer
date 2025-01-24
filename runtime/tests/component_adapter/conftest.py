import os
from unittest import mock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from hetdesrun.persistence.dbservice.revision import store_single_transformation_revision
from hetdesrun.trafoutils.io.load import transformation_revision_from_python_code
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="session")
def app_without_auth() -> FastAPI:
    with mock.patch("hetdesrun.webservice.config.runtime_config.auth", False):
        yield init_app()


@pytest.fixture
def async_test_client_for_component_adapter_tests(
    app_without_auth: FastAPI,
) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app_without_auth), base_url="http://test")


@pytest_asyncio.fixture
async def open_async_test_client_for_component_adapter_tests(
    async_test_client_for_component_adapter_tests,
):
    async with async_test_client_for_component_adapter_tests as client:
        yield client


def trafo_from_py_file_into_db(py_file_path: str):
    with open(py_file_path) as f:
        code = f.read()

    tr_from_py = transformation_revision_from_python_code(code)

    store_single_transformation_revision(tr_from_py)


@pytest.fixture
def _components_for_component_adapter_tests(mocked_clean_test_db_session):
    py_file_path = os.path.join(
        "tests",
        "data",
        "components",
        "random-timeseries-data.py",
    )  # Draft

    py_file_path2 = os.path.join(
        "tests",
        "data",
        "components",
        "reduced_code.py",
    )  # Released

    py_file_path3 = os.path.join(
        "tests",
        "data",
        "components",
        "pass_trough_any_disabled.py",
    )  # Disabled / deprecated

    py_file_path4 = os.path.join(
        "tests",
        "data",
        "components",
        "test_comp_code_repr.py",
    )

    trafo_from_py_file_into_db(py_file_path)
    trafo_from_py_file_into_db(py_file_path2)
    trafo_from_py_file_into_db(py_file_path3)
    trafo_from_py_file_into_db(py_file_path4)


@pytest.fixture
def _pass_through_str(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "pass_through_str.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)


@pytest.fixture
def _markdown_file_component_sink(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "markdown_file.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)


@pytest.fixture
def _pass_through_multits_component_in_db(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "pass_through_multits.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)


@pytest.fixture
def _plotly_to_html_file_sink_component(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "plotly_to_html_file.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)


@pytest.fixture
def _single_timeseries_plot_component(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "single_timeseries_plot.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)
