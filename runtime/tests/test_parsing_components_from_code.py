import json
import os

import pytest

from hetdesrun.backend.execution import ExecByIdInput
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import transformation_revision_from_python_code


@pytest.mark.asyncio
async def test_default_values_with_metadata(async_test_client, mocked_clean_test_db_session):
    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_comp_code_repr.py",
    )
    with open(py_path) as f:
        code = f.read()

    tr_from_py = transformation_revision_from_python_code(code)

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


def load_check_from_code_file(code_file_path: str) -> (str, TransformationRevision):
    with open(code_file_path) as f:
        code = f.read()
    tr_from_py = transformation_revision_from_python_code(code)

    assert tr_from_py.content == code

    return code, tr_from_py


def load_check_from_json_file(json_file_path: str) -> TransformationRevision:
    with open(json_file_path) as f:
        trafo = TransformationRevision(**json.load(f))

    tr_from_content = transformation_revision_from_python_code(trafo.content)
    assert tr_from_content.dict() == trafo

    return trafo


async def put_trafo_via_multiple_put_endpoint(
    trafo: str | TransformationRevision,
    open_async_client,
    update_code=True,
    trafo_id=None,
):
    if trafo_id is None:
        trafo_id = trafo.id
    response = await open_async_client.put(
        "/api/transformations",
        params={"overwrite_released": True, "update_code": update_code},
        json=[json.loads(trafo.json()) if isinstance(trafo, TransformationRevision) else trafo],
    )
    assert response.status_code == 207
    assert response.json()[str(trafo_id)]["status"] == "SUCCESS"


async def put_trafo_via_single_put_endpoint(
    trafo: TransformationRevision, open_async_client, update_code=True
):
    response = await open_async_client.put(
        f"/api/transformations/{str(trafo.id)}",
        params={"overwrite_released": True, "update_code": update_code},
        json=json.loads(trafo.json()),
    )
    assert response.status_code == 201


async def get_check_trafo_via_single_id_get_endpoint(
    trafo: TransformationRevision, open_async_client
) -> TransformationRevision:
    response = await open_async_client.get(f"/api/transformations/{str(trafo.id)}")
    assert response.status_code == 200

    tr_from_resp = TransformationRevision(**response.json())

    assert tr_from_resp == trafo

    tr_from_response_content_json_obj = transformation_revision_from_python_code(
        response.json()["content"]
    )
    assert tr_from_response_content_json_obj == trafo
    return trafo


async def get_check_trafo_via_multiple_get_endpoint(
    trafo,
    open_async_client,
    update_code: bool = True,
    expand_code: bool = True,
    components_as_code: bool = False,
):
    response = await open_async_client.get(
        f"/api/transformations?id={str(trafo.id)}",
        params={
            "expand_component_code": expand_code,
            "update_component_code": update_code,
            "components_as_code": components_as_code,
        },
    )
    assert response.status_code == 200

    if not components_as_code:
        got_trafo_json_ob = response.json()[0]
        tr_from_resp = TransformationRevision(**got_trafo_json_ob)
        code_from_response = tr_from_resp.content
    else:
        code_from_response = response.json()[0]
        tr_from_resp = transformation_revision_from_python_code(code_from_response)

    assert tr_from_resp == trafo
    assert code_from_response == trafo.content

    tr_from_response_content_json_obj = transformation_revision_from_python_code(
        tr_from_resp.content
    )
    assert tr_from_response_content_json_obj == trafo


@pytest.mark.asyncio
async def test_component_trafo_code_equivalence(async_test_client, mocked_clean_test_db_session):
    example_py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_comp_code_repr.py",
    )

    second_example_pa_path = os.path.join(
        "tests",
        "data",
        "components",
        "expanded_code.py",
    )

    async with async_test_client as ac:
        for py_path in [example_py_path, second_example_pa_path]:
            code, tr_from_py = load_check_from_code_file(py_path)
            await put_trafo_via_multiple_put_endpoint(tr_from_py, ac)
            await get_check_trafo_via_single_id_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac, components_as_code=True)

            await put_trafo_via_multiple_put_endpoint(code, ac, trafo_id=tr_from_py.id)
            await get_check_trafo_via_single_id_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac, components_as_code=True)

            await put_trafo_via_single_put_endpoint(tr_from_py, ac)
            await get_check_trafo_via_single_id_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac)
            await get_check_trafo_via_multiple_get_endpoint(tr_from_py, ac, components_as_code=True)
