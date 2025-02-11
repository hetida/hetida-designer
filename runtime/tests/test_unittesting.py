import os

import pytest

from hetdesrun.persistence.dbservice.revision import store_single_transformation_revision
from hetdesrun.runtime.unittesting import unittest_code
from hetdesrun.trafoutils.io.load import transformation_revision_from_python_code


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


@pytest.mark.asyncio
@pytest.mark.usefixtures("_to_wide_format_component_in_db")
async def test_unittest_endpoint(mocked_clean_test_db_session, open_async_test_client):
    component_id = "327fc07a-1b3f-4c99-a9aa-0f9b2130cdef"
    resp = await open_async_test_client.post(f"api/transformations/{component_id}/test")

    assert resp.status_code == 200
    assert "passed" in resp.json()["pytest_stdout_str"]
