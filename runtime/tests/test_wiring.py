from starlette.testclient import TestClient
from hetdesrun.service.webservice import app

client = TestClient(app)


def run_workflow_with_client(workflow_json):
    response = client.post("/runtime", json=workflow_json)
    return response.status_code, response.json()


def test_wiring_basics(input_json_with_wiring):
    status_code, output = run_workflow_with_client(input_json_with_wiring)

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
            "filters": {"value": 42},
        }
    ]
    status_code, output = run_workflow_with_client(input_json_with_wiring)
    assert status_code == 422

    # but for all workflow inputs / outputs there must be a wiring!
    input_json_with_wiring["workflow_wiring"]["output_wirings"] = []
    status_code, output = run_workflow_with_client(input_json_with_wiring)

    assert status_code == 422  # incomplete wiring


def test_wiring_direct_input_provisioning(input_json_with_wiring_with_input):
    status_code, output = run_workflow_with_client(input_json_with_wiring_with_input)

    assert status_code == 200

    node_results = output["node_results"]

    assert "32.0" in node_results  # intermediate result
    assert "64.0" in node_results
