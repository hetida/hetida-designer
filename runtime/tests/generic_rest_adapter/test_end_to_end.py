from unittest import mock
from copy import deepcopy

from starlette.testclient import TestClient
from hetdesrun.service.webservice import app

from hetdesrun.models.wiring import WorkflowWiring

client = TestClient(app)


def run_workflow_with_client(workflow_json):
    response = client.post("/runtime", json=workflow_json)
    return response.status_code, response.json()


def test_wiring_with_generic_rest_input(
    input_json_with_wiring_with_input,
):

    json_with_wiring = deepcopy(input_json_with_wiring_with_input)
    json_with_wiring["workflow_wiring"]["input_wirings"] = [
        {
            "workflow_input_name": "val_inp",
            "adapter_id": "gen_rest_adapter_test_id",
            "ref_id": "thing_node_id",
            "ref_id_type": "THINGNODE",
            "ref_key": "number",
            "type": "metadata(int)",
        }
    ]

    ww = WorkflowWiring(**json_with_wiring["workflow_wiring"])

    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(
        return_value={"key": "number", "value": 32, "dataType": "int"}
    )
    with mock.patch(
        "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
        return_value="https://hetida.de",
    ):
        with mock.patch(
            "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
            return_value=resp_mock,
        ) as mocked_async_client_get:
            status_code, output = run_workflow_with_client(json_with_wiring)

            assert status_code == 200

            node_results = output["node_results"]

            assert "32.0" in node_results  # intermediate result
            assert "64.0" in node_results

            # now add sending metadata from the only output
            json_with_wiring["workflow_wiring"]["output_wirings"] = [
                {
                    "workflow_output_name": "z",
                    "adapter_id": "gen_rest_adapter_test_id",
                    "ref_id": "thing_node_id",
                    "ref_id_type": "THINGNODE",
                    "ref_key": "limit",
                    "type": "metadata(float)",
                }
            ]
            with mock.patch(
                "hetdesrun.adapters.generic_rest.send_metadata.get_generic_rest_adapter_base_url",
                return_value="https://hetida.de",
            ):
                response = mock.Mock()
                response.status_code = 200
                post_mock = mock.AsyncMock(return_value=response)

                with mock.patch(
                    "hetdesrun.adapters.generic_rest.send_metadata.httpx.AsyncClient.post",
                    new=post_mock,
                ):
                    status_code, output = run_workflow_with_client(json_with_wiring)
                    func_name, args, kwargs = post_mock.mock_calls[0]

                    assert kwargs["json"] == (
                        {"key": "limit", "value": 64.0, "dataType": "float"}
                    )
                    assert (
                        args[0]
                        == "https://hetida.de/thingNodes/thing_node_id/metadata/limit"
                    )
