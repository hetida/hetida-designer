import os

import pytest

from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.mark.asyncio
async def test_get_transitive_imported_components_when_fetching_with_include_dependencies(
    mocked_clean_test_db_session, async_test_client
):
    with TrafoCollection(save_to_db=True) as tc:
        comp_with_funcs = tc.add_from_py_file(  # noqa: F841
            os.path.join(
                "tests",
                "data",
                "components",
                "component_with_functions_for_importing.py",
            )
        )
        comp_importing_a_func = tc.add_from_py_file(  # noqa: F841
            os.path.join(
                "tests",
                "data",
                "components",
                "component_importing_func_from_other.py",
            )
        )
        comp_2_level_import = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "component_2_level_import.py",
            )
        )

    async with async_test_client as ac:
        # with include_dependencies True:
        resp = await ac.get(
            "/api/transformations",
            params={"include_dependencies": True, "id": str(comp_2_level_import.id)},
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        # get all three
        assert len(resp_json) == 3

        # with include_dependencies True:
        resp = await ac.get(
            "/api/transformations",
            params={
                "include_dependencies": True,
                "id": str(comp_importing_a_func.id),  # middle one
            },
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        # get first two
        assert len(resp_json) == 2

        # with include_dependencies False:
        resp = await ac.get(
            "/api/transformations",
            params={"include_dependencies": False, "id": str(comp_2_level_import.id)},
        )
        resp_json = resp.json()
        # get only the one requested
        assert len(resp_json) == 1
