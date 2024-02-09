import json
import os

import pytest

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import transformation_revision_from_python_code


@pytest.mark.asyncio
async def test_default_values_with_metadata(
    async_test_client, mocked_clean_test_db_session
):
    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_comp_code_repr.py",
    )
    with open(py_path) as f:
        code = f.read()

    tr_from_py_json = transformation_revision_from_python_code(code)
    tr_from_py = TransformationRevision(**tr_from_py_json)

    exec_by_id_input = ExecByIdInput(
        id=tr_from_py.id,
        wiring=tr_from_py.test_wiring,
    )
    async with async_test_client as ac:
        response = await ac.put(
            "/api/transformations",
            json=[json.loads(tr_from_py.json())],
        )
        assert response.status_code == 207
        assert response.json()[str(tr_from_py.id)]["status"] == "SUCCESS"

        response = await ac.post(
            "/api/transformations/execute",
            json=json.loads(exec_by_id_input.json()),
        )

    assert response.status_code == 200
    resp_data = response.json()
    output_data = resp_data["output_results_by_output_name"]
    assert output_data["multitsframe"]["__metadata__"] == {"test": 43}
    assert output_data["empty_string_any"] == ""
    assert output_data["some_string_any"] == "text"
    assert output_data["some_number_any"] == 23
    assert output_data["null_any"] is None
    assert output_data["null_text"] == "null"

    assert output_data["series"]["__metadata__"] == {}


@pytest.mark.asyncio
async def test_equivalence_component_representations(  # noqa: PLR0915
    async_test_client, mocked_clean_test_db_session
):
    """Test identities when switching between code and Trafo object representation

    When passing a trafo back and forth through put (whether as trafo json or as code)
    and get, both representations (code or trafo json) should be preserved.
    """
    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_comp_code_repr.py",
    )
    with open(py_path) as f:
        code = f.read()

    tr_from_py_json = transformation_revision_from_python_code(code)
    tr_from_py = TransformationRevision(**tr_from_py_json)

    assert len(tr_from_py.test_wiring.input_wirings) == 1
    assert tr_from_py.test_wiring.input_wirings[0].filters["value"] == "45.6"

    async with async_test_client as ac:
        # put as json
        response = await ac.put(
            "/api/transformations?update_component_code=true&overwrite_released=true",
            json=[json.loads(tr_from_py.json())],
        )
        assert response.status_code == 207
        assert response.json()[str(tr_from_py.id)]["status"] == "SUCCESS"

        # get from explicit id endpoint
        response = await ac.get(f"/api/transformations/{str(tr_from_py.id)}")
        assert response.status_code == 200

        tr_from_resp = TransformationRevision(**response.json())

        assert tr_from_resp == tr_from_py
        assert tr_from_resp.content == code

        tr_from_response_content_json_obj = transformation_revision_from_python_code(
            response.json()["content"]
        )
        assert TransformationRevision(**tr_from_response_content_json_obj) == tr_from_py

        # get from multiple trafo get endpoint with code upgrades
        response = await ac.get(
            f"/api/transformations?id={str(tr_from_py.id)}&expand_component_code=true&update_component_code=true"
        )
        assert response.status_code == 200
        got_trafo_json_ob = response.json()[0]

        tr_from_resp = TransformationRevision(**got_trafo_json_ob)

        assert tr_from_resp == tr_from_py
        assert tr_from_resp.content == code

        tr_from_response_content_json_obj = transformation_revision_from_python_code(
            tr_from_resp.content
        )
        assert TransformationRevision(**tr_from_response_content_json_obj) == tr_from_py

        # get from multiple trafo get endpoint with code upgrades returning code
        response = await ac.get(
            f"/api/transformations?id={str(tr_from_py.id)}&expand_component_code=true&update_component_code=true&components_as_code=true"
        )
        assert response.status_code == 200
        got_trafo_code_str = response.json()[0]
        assert got_trafo_code_str == code

        trafo_json_obj_from_response_code = transformation_revision_from_python_code(
            tr_from_resp.content
        )
        assert TransformationRevision(**trafo_json_obj_from_response_code) == tr_from_py

        # put as code
        response = await ac.put(
            "/api/transformations?update_component_code=true&overwrite_released=true",
            json=[code],
        )
        assert response.status_code == 207
        assert response.json()[str(tr_from_py.id)]["status"] == "SUCCESS"

        response = await ac.get(f"/api/transformations/{str(tr_from_py.id)}")
        assert response.status_code == 200

        tr_from_resp = TransformationRevision(**response.json())

        assert tr_from_resp == tr_from_py
        assert tr_from_resp.content == code

        tr_from_response_content_json_obj = transformation_revision_from_python_code(
            response.json()["content"]
        )
        assert TransformationRevision(**tr_from_response_content_json_obj) == tr_from_py

        # get from multiple trafo get endpoint with code upgrades
        response = await ac.get(
            f"/api/transformations?id={str(tr_from_py.id)}&expand_component_code=true&update_component_code=true"
        )
        assert response.status_code == 200
        got_trafo_json_ob = response.json()[0]

        tr_from_resp = TransformationRevision(**got_trafo_json_ob)

        assert tr_from_resp == tr_from_py
        assert tr_from_resp.content == code

        tr_from_response_content_json_obj = transformation_revision_from_python_code(
            tr_from_resp.content
        )
        assert TransformationRevision(**tr_from_response_content_json_obj) == tr_from_py

        # get from multiple trafo get endpoint with code upgrades returning code
        response = await ac.get(
            f"/api/transformations?id={str(tr_from_py.id)}&expand_component_code=true&update_component_code=true&components_as_code=true"
        )
        assert response.status_code == 200
        got_trafo_code_str = response.json()[0]
        assert got_trafo_code_str == code

        trafo_json_obj_from_response_code = transformation_revision_from_python_code(
            tr_from_resp.content
        )
        assert TransformationRevision(**trafo_json_obj_from_response_code) == tr_from_py
