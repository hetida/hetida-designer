import os

import pytest

from hetdesrun.persistence.dbservice.revision import store_single_transformation_revision
from hetdesrun.runtime.unittesting import unittest_code
from hetdesrun.trafoutils.io.load import transformation_revision_from_python_code
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


def trafo_from_py_file_into_db(py_file_path: str):
    with open(py_file_path) as f:
        code = f.read()

    tr_from_py = transformation_revision_from_python_code(code)

    store_single_transformation_revision(tr_from_py)


@pytest.fixture
def _to_wide_format_component_in_db(mocked_clean_test_db_session):
    path_to_py_file_present = os.path.join(
        "tests",
        "data",
        "components",
        "to_wide_format.py",
    )
    trafo_from_py_file_into_db(path_to_py_file_present)


def test_basic_unittesting():
    result = unittest_code(r"""

def test_passing_example():
    pass

def test_failing_example():
    assert False

    """)

    assert "1 passed" in result.pytest_stdout_str
    assert "1 failed" in result.pytest_stdout_str


def test_doctests():
    result = unittest_code(r'''

def my_func():
    """My function

    >>> my_func()
    42
    >>> my_func() - 42
    0
    """
    return 42

def my_second_func():
    """My second_function

    >>> my_second_func()
    11
    """
    return 11

    ''')

    assert "2 passed" in result.pytest_stdout_str


def test_unittesting_with_hetdesrun_and_hdutils_imports():
    """hetdesrun and hdutils must be importable in the pytest process

    They are not installed as packages, so the pytest process needs the runtime
    base directory on its PYTHONPATH.
    """
    result = unittest_code(r"""
from hdutils import parse_default_value  # noqa: F401
from hetdesrun.models.code import CodeModule


def test_using_hetdesrun_import():
    code_module = CodeModule(code="x = 42", uuid="327fc07a-1b3f-4c99-a9aa-0f9b2130cdef")
    assert code_module.code == "x = 42"

    """)

    assert "1 passed" in result.pytest_stdout_str


def test_unittesting_with_component_imports():
    """import_comp in component code must work during unittesting"""
    path_to_py_file = os.path.join(
        "tests",
        "data",
        "components",
        "component_with_functions_for_importing.py",
    )
    with open(path_to_py_file) as f:
        code = f.read()

    imported_trafo = transformation_revision_from_python_code(code)

    result = unittest_code(
        r"""
from hetdesrun.component.load import import_comp
module_exposing_func = import_comp("60ae0402-44cb-4f01-9b16-f1053e8f116c")


def test_imported_func():
    assert module_exposing_func.my_exposed_func(21) == 42

    """,
        code_modules=[imported_trafo.to_code_module()],
        components=[imported_trafo.to_component_revision()],
    )

    assert "1 passed" in result.pytest_stdout_str


def test_unittesting_missing_component_import_shows_up_in_pytest_output():
    result = unittest_code(r"""
from hetdesrun.component.load import import_comp
module_exposing_func = import_comp("60ae0402-44cb-4f01-9b16-f1053e8f116c")
    """)

    assert "Missing component revision" in result.pytest_stdout_str


@pytest.mark.asyncio
@pytest.mark.usefixtures("_to_wide_format_component_in_db")
async def test_unittest_endpoint(mocked_clean_test_db_session, open_async_test_client):
    component_id = "327fc07a-1b3f-4c99-a9aa-0f9b2130cdef"
    resp = await open_async_test_client.post(f"api/transformations/{component_id}/test")

    assert resp.status_code == 200
    assert "passed" in resp.json()["pytest_stdout_str"]


@pytest.mark.asyncio
async def test_unittest_endpoint_with_component_imports(
    mocked_clean_test_db_session, open_async_test_client
):
    with TrafoCollection(save_to_db=True) as tc:
        tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_with_functions_for_importing.py",
            )
        )
        comp_importing_with_tests = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_importing_func_with_tests.py",
            )
        )

    resp = await open_async_test_client.post(
        f"api/transformations/{comp_importing_with_tests.id}/test"
    )

    assert resp.status_code == 200
    assert "2 passed" in resp.json()["pytest_stdout_str"]
