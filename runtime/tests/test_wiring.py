import json
import os
from urllib.parse import quote_plus

import pytest

from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


async def run_workflow_with_client(workflow_json, open_async_test_client):
    response = await open_async_test_client.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


@pytest.mark.asyncio
async def test_wiring_basics(input_json_with_wiring, async_test_client):
    async with async_test_client as client:
        status_code, output = await run_workflow_with_client(input_json_with_wiring, client)

        assert status_code == 200

        assert output["result"] == "ok"

        node_results = output["node_results"]

        assert "2.0" in node_results
        assert "4.0" in node_results

        # does returning via direct sink provisioning work?
        assert output["output_results_by_output_name"]["z"] == 4.0

        # providing too many input wirings raises validation error
        input_json_with_wiring["workflow_wiring"]["input_wirings"] = [
            {
                "workflow_input_name": "foo",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": "42"},
            }
        ]
        status_code, output = await run_workflow_with_client(input_json_with_wiring, client)
        assert status_code == 422

        # but for all workflow inputs / outputs there must be a wiring!
        input_json_with_wiring["workflow_wiring"]["output_wirings"] = []
        status_code, output = await run_workflow_with_client(input_json_with_wiring, client)

        assert status_code == 422  # incomplete wiring


@pytest.mark.asyncio
async def test_wiring_direct_input_provisioning(
    input_json_with_wiring_with_input, async_test_client
):
    async with async_test_client as client:
        status_code, output = await run_workflow_with_client(
            input_json_with_wiring_with_input, client
        )

        assert status_code == 200

        node_results = output["node_results"]

        assert "32.0" in node_results  # intermediate result
        assert "64.0" in node_results


@pytest.mark.asyncio
async def test_uri_input_wiring(mocked_clean_test_db_session, async_test_client):
    with TrafoCollection(save_to_db=True) as tc:
        pass_trough_int = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
            )
        )

    async with async_test_client as ac:
        exec_input = ExecByIdInput(
            id=pass_trough_int.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "uri": f"hd://component-adapter/{pass_trough_int.id}?input=55",
                        "workflow_input_name": "input",
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["output"] == 55

        # test filter from uri has higehr priority
        exec_input = ExecByIdInput(
            id=pass_trough_int.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "uri": f"hd://component-adapter/{pass_trough_int.id}?input=55",
                        "workflow_input_name": "input",
                        "filters": {"input": 21},
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["output"] == 55

        # test filter can be provided out of uri as well
        exec_input = ExecByIdInput(
            id=pass_trough_int.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "uri": f"hd://component-adapter/{pass_trough_int.id}",
                        "workflow_input_name": "input",
                        "filters": {"input": 21},
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["output"] == 21


@pytest.mark.asyncio
async def test_uri_input_default_wiring_variants(mocked_clean_test_db_session, async_test_client):
    """What happens if filters are not set in URI wiring for inputs with default values

    Then the default value should be used correctly.
    """
    with TrafoCollection(save_to_db=True) as tc:
        pass_trough = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json",
            )
        )
        default_variants = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "input_default_value_variants.py",
            )
        )

    async with async_test_client as ac:
        exec_input = ExecByIdInput(
            id=pass_trough.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "uri": f"hd://component-adapter/{default_variants.id}?inp_bool_required=false",
                        "workflow_input_name": "input",
                    }
                ]
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["output"] == {
            "inp_bool_default_actual_null": None,
            # string rep "null" as default is interpreted correctly as None:
            "inp_bool_default_null_string": None,
            "inp_bool_required": False,
            "inp_bool_default_true": True,
            "inp_bool_default_false": False,
        }


@pytest.mark.asyncio
async def test_uri_output_wiring(mocked_clean_test_db_session, async_test_client, tmpdir):
    target_path = tmpdir / "out_file.md"

    with TrafoCollection(save_to_db=True) as tc:
        pass_trough_int = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
            )
        )
        pass_trough_str = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )
        markdown_file_component_sink = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "markdown_file.py",
            )
        )

    async with async_test_client as ac:
        exec_input = ExecByIdInput(
            id=pass_trough_int.id,
            job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
            wiring=WorkflowWiring(
                input_wirings=[
                    {
                        "workflow_input_name": "input",
                        "filters": {"value": 42},
                    }
                ],
                output_wirings=[
                    {"workflow_output_name": "output", "uri": "hd://direct_provisioning"}
                ],
            ),
        )
        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )
        assert resp.status_code == 200

        resp_json = resp.json()
        assert resp_json["output_results_by_output_name"]["output"] == 42

        # output wiring different from direct_provisioning
        exec_input = ExecByIdInput(
            id=pass_trough_str.id,
            wiring={
                "input_wirings": [
                    {
                        "workflow_input_name": "input",
                        "adapter_id": "direct_provisioning",
                        "filters": {"value": "test"},
                    }
                ],
                "output_wirings": [
                    {
                        "workflow_output_name": "output",
                        "uri": f"hd://component-adapter/{markdown_file_component_sink.id}?path={quote_plus(str(target_path))}",
                    }
                ],
            },
        )

        resp = await ac.post(
            "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
        )

        assert resp.status_code == 200
        assert resp.json()["error"] is None
        assert len(resp.json()["output_results_by_output_name"]) == 0  # no outputs
