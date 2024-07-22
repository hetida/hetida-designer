from copy import deepcopy
from unittest import mock

import pytest

from hetdesrun.models.wiring import WorkflowWiring


async def run_workflow_with_client(workflow_json, open_async_test_client):
    response = await open_async_test_client.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


@pytest.mark.asyncio
async def test_wiring_with_generic_rest_input(input_json_with_wiring_with_input, async_test_client):
    async with async_test_client as client:
        json_with_wiring = deepcopy(input_json_with_wiring_with_input)
        json_with_wiring["workflow_wiring"]["input_wirings"] = [
            {
                "workflow_input_name": "val_inp",
                "adapter_id": "gen_rest_adapter_test_id",
                "ref_id": "thing_node_id",
                "ref_id_type": "THINGNODE",
                "ref_key": "number",
                "type": "metadata(float)",
            }
        ]

        # check parsable as WorkflowWiring:
        ww = WorkflowWiring(**json_with_wiring["workflow_wiring"])  # noqa: F841

        resp_mock = mock.Mock()
        resp_mock.status_code = 200
        resp_mock.json = mock.Mock(return_value={"key": "number", "value": 32, "dataType": "float"})
        with mock.patch(  # noqa: SIM117
            "hetdesrun.adapters.generic_rest.load_metadata.get_generic_rest_adapter_base_url",
            return_value="https://hetida.de",
        ):
            with mock.patch(
                "hetdesrun.adapters.generic_rest.load_metadata.httpx.AsyncClient.get",
                return_value=resp_mock,
            ) as _mocked_async_client_get:
                status_code, output = await run_workflow_with_client(json_with_wiring, client)

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
                        "filters": {"filter_key": "filter_value"},
                    }
                ]
                with mock.patch(
                    "hetdesrun.adapters.generic_rest.send_metadata.get_generic_rest_adapter_base_url",
                    return_value="https://hetida.de",
                ):
                    response = mock.Mock()
                    response.status_code = 200
                    send_metadata_post_mock = mock.AsyncMock(return_value=response)

                    with mock.patch(
                        "hetdesrun.adapters.generic_rest.send_metadata.post_json_with_open_client",
                        new=send_metadata_post_mock,
                    ):
                        status_code, output = await run_workflow_with_client(
                            json_with_wiring, client
                        )
                        # what gets into the post request sent from send_metadata:
                        _, _, kwargs = send_metadata_post_mock.mock_calls[0]

                        assert kwargs["json_payload"] == (
                            {"key": "limit", "value": 64.0, "dataType": "float"}
                        )
                        assert (
                            kwargs["url"]
                            == "https://hetida.de/thingNodes/thing_node_id/metadata/limit"
                        )
                        assert kwargs["params"] == {"filter_key": "filter_value"}
