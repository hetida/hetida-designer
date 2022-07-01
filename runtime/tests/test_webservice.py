import warnings

from copy import deepcopy

# the following line in hetdesrun.webservice.application causes a DeprecationWarning concerning
# imp module usage:
#    from fastapi import FastAPI
# Therefore we ignore such warnings here
warnings.filterwarnings("ignore", message="the imp module is deprecated")

from starlette.testclient import TestClient

import pytest

from hetdesrun.webservice.application import app

from hetdesrun.utils import get_uuid_from_seed

client = TestClient(app)


@pytest.mark.asyncio
async def test_swagger_ui_available(async_test_client):
    async with async_test_client as ac:
        response = await ac.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


# def test_swagger_ui_available_2():
#     response = client.get("/docs")

#     assert response.status_code == 200
#     assert "swagger-ui" in response.text.lower()


@pytest.mark.asyncio
async def test_access_api_endpoint(async_test_client):
    async with async_test_client as ac:
        response = await ac.post(
            "engine/codegen",
            json={
                "inputs": [],
                "outputs": [],
                "code": "",
                "function_name": "main",
                "name": "Testname",
                "description": "Test Descr.",
                "category": "Test category",
                "id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
                "revision_group_id": "c6eff22c-21c4-43c6-9ae1-b2bdfb944565",
                "version_tag": "1.0.0",
            },
        )
    assert response.status_code == 200
    assert "code" in response.json().keys()


base_workflow_json = {
    "code_modules": [
        {  # ordinary function entry point
            "uuid": str(get_uuid_from_seed("my_code_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Float, "y": DataType.Float}, outputs={"z": DataType.Float}\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": x+y}',
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Float}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": 2.0}',
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "inputs": [
                {
                    "name": "x",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("x_in_my_component")),
                },
                {
                    "name": "y",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("y_in_my_component")),
                },
            ],
            "outputs": [
                {
                    "name": "z",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("z_in_my_component")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("my_code_module")),
            "function_name": "main",
        },
        {
            "uuid": str(get_uuid_from_seed("my_const_giver")),
            "inputs": [],
            "outputs": [
                {
                    "name": "c",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("c_in_my_const_giver")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("const_giver_module")),
            "function_name": "main",
        },
    ],
    "workflow": {
        "id": str(get_uuid_from_seed("my_workflow")),
        "connections": [
            {
                "input_in_workflow_id": str(get_uuid_from_seed("1001")),
                "input_name": "c",
                "input_id": str(get_uuid_from_seed("input_c_in_1001")),
                "output_in_workflow_id": str(get_uuid_from_seed("1000")),
                "output_name": "x",
                "output_id": str(get_uuid_from_seed("output_c_in_1000")),
            },
            {
                "input_in_workflow_id": str(get_uuid_from_seed("1001")),
                "input_name": "c",
                "input_id": str(get_uuid_from_seed("input_c_in_1001")),
                "output_in_workflow_id": str(get_uuid_from_seed("1000")),
                "output_name": "y",
                "output_id": str(get_uuid_from_seed("output_y_in_1000")),
            },
        ],
        "inputs": [],
        "outputs": [
            {
                "name": "z",
                "id": str(get_uuid_from_seed("output_z_in_1000")),
                "type": "FLOAT",
                "name_in_subnode": "z",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            }
        ],
        "sub_nodes": [
            {
                "id": str(get_uuid_from_seed("1000")),
                "component_uuid": str(get_uuid_from_seed("my_component")),
            },
            {
                "id": str(get_uuid_from_seed("1001")),
                "component_uuid": str(get_uuid_from_seed("my_const_giver")),
            },
        ],
    },
    "configuration": {
        "name": "string",
        "engine": "plain",
        "return_individual_node_results": True,
    },
    "workflow_wiring": {
        "input_wirings": [],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    },
}


async def run_workflow_with_client(workflow_json, async_test_client):
    async with async_test_client as ac:
        response = await ac.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


@pytest.mark.asyncio
async def test_running_workflow(async_test_client):

    status_code, output = await run_workflow_with_client(
        base_workflow_json.copy(), async_test_client
    )

    assert status_code == 200
    assert output["result"] == "ok"

    node_results = output["node_results"]
    assert "2.0" in node_results
    assert "4.0" in node_results


series_input_workflow_json = {
    "code_modules": [
        {
            "uuid": str(get_uuid_from_seed("my_code_module_series")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Series, "y": DataType.Float}, outputs={"z": DataType.DataFrame}\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": x.to_frame() + y}',
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Float}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": 2.0}',
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "inputs": [
                {
                    "name": "x",
                    "type": "SERIES",
                    "id": str(get_uuid_from_seed("x_in_my_component")),
                },
                {
                    "name": "y",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("y_in_my_component")),
                },
            ],
            "outputs": [
                {
                    "name": "z",
                    "type": "DATAFRAME",
                    "id": str(get_uuid_from_seed("z_in_my_component")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("my_code_module_series")),
            "function_name": "main",
        },
        {
            "uuid": str(get_uuid_from_seed("my_const_giver")),
            "inputs": [],
            "outputs": [
                {
                    "name": "c",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("c_in_my_const_giver")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("const_giver_module")),
            "function_name": "main",
        },
    ],
    "workflow": {
        "id": str(get_uuid_from_seed("my_workflow")),
        "connections": [
            {
                "input_in_workflow_id": str(get_uuid_from_seed("1001")),
                "input_name": "c",
                "input_id": str(get_uuid_from_seed("input_c_in_1001")),
                "output_in_workflow_id": str(get_uuid_from_seed("1000")),
                "output_name": "y",
                "output_id": str(get_uuid_from_seed("output_y_in_1000")),
            }
        ],
        "inputs": [
            {
                "name": "x",
                "id": str(get_uuid_from_seed("workflow_input_to_x_in_my_component")),
                "type": "SERIES",
                "name_in_subnode": "x",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            }
        ],
        "outputs": [
            {
                "name": "z",
                "id": str(get_uuid_from_seed("output_z_in_1000")),
                "type": "DATAFRAME",
                "name_in_subnode": "z",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            }
        ],
        "sub_nodes": [
            {
                "id": str(get_uuid_from_seed("1000")),
                "component_uuid": str(get_uuid_from_seed("my_component")),
            },
            {
                "id": str(get_uuid_from_seed("1001")),
                "component_uuid": str(get_uuid_from_seed("my_const_giver")),
            },
        ],
    },
    "configuration": {"name": "string", "engine": "plain"},
    "workflow_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "x",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": [1.0, 2.0, 3.5]},
            }
        ],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    },
}


@pytest.mark.asyncio
async def test_workflow_with_series_input_and_dataframe_output(async_test_client):
    status_code, output = await run_workflow_with_client(
        series_input_workflow_json.copy(), async_test_client
    )

    assert status_code == 200
    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"]["0"] == {
        "0": 3.0,
        "1": 4.0,
        "2": 5.5,
    }


single_node_input_workflow_json = {
    "code_modules": [
        {
            "uuid": str(get_uuid_from_seed("single_node_code")),
            "code": (
                '''\
from hetdesrun.component.registration import register
from hetdesrun.datatypes import DataType
import logging
test_logger = logging.getLogger(__name__)
# add your own imports here

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if input/output changes.
@register(
    inputs={"x": DataType.DataFrame, "y": DataType.Float}, outputs={"z": DataType.Series}
)
def main(*, x, y):
    """entrypoint function for this component"""
    test_logger.info("TEST in component funct " + __name__)
    # print(1 /
    # ***** NOT EDIT LINES ABOVE *****
    # wriyour function code here.
    pass
    return {"z": x.squeeze() + y}
'''
            ),
        }
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "inputs": [
                {
                    "name": "x",
                    "type": "DATAFRAME",
                    "id": str(get_uuid_from_seed("x_in_my_component")),
                },
                {
                    "name": "y",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("y_in_my_component")),
                },
            ],
            "outputs": [
                {
                    "name": "z",
                    "type": "SERIES",
                    "id": str(get_uuid_from_seed("z_in_my_component")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("single_node_code")),
            "function_name": "main",
        }
    ],
    "workflow": {
        "id": str(get_uuid_from_seed("my_workflow")),
        "connections": [],
        "inputs": [
            {
                "name": "x",
                "id": str(get_uuid_from_seed("workflow_input_to_x_in_my_component")),
                "type": "DATAFRAME",
                "name_in_subnode": "x",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            },
            {
                "name": "y",
                "id": str(get_uuid_from_seed("workflow_input_to_y_in_my_component")),
                "type": "FLOAT",
                "name_in_subnode": "y",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            },
        ],
        "outputs": [
            {
                "name": "z",
                "id": str(get_uuid_from_seed("output_z_in_1000")),
                "type": "SERIES",
                "name_in_subnode": "z",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            }
        ],
        "sub_nodes": [
            {
                "id": str(get_uuid_from_seed("1000")),
                "component_uuid": str(get_uuid_from_seed("my_component")),
            }
        ],
    },
    "configuration": {"name": "string", "engine": "plain"},
    "workflow_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "x",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": {"a": [1.0, 2.0, 3.5]}},
            },
            {
                "workflow_input_name": "y",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": 2.0},
            },
        ],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    },
}


@pytest.mark.asyncio
async def test_single_node_workflow_with_dataframe_input_and_series_output(
    async_test_client,
):
    status_code, output = await run_workflow_with_client(
        single_node_input_workflow_json.copy(), async_test_client
    )

    assert status_code == 200

    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"] == {
        "0": 3.0,
        "1": 4.0,
        "2": 5.5,
    }


plot_workflow_json = {
    "code_modules": [
        {  # ordinary function entry point
            "uuid": str(get_uuid_from_seed("my_code_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Float, "y": DataType.Float}, outputs={"z": DataType.PlotlyJson}, is_pure_plot_component=True\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": {"a": 1.0}}',
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Float}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": 2.0}',
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "inputs": [
                {
                    "name": "x",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("x_in_my_component")),
                },
                {
                    "name": "y",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("y_in_my_component")),
                },
            ],
            "outputs": [
                {
                    "name": "z",
                    "type": "PLOTLYJSON",
                    "id": str(get_uuid_from_seed("z_in_my_component")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("my_code_module")),
            "function_name": "main",
        },
        {
            "uuid": str(get_uuid_from_seed("my_const_giver")),
            "inputs": [],
            "outputs": [
                {
                    "name": "c",
                    "type": "FLOAT",
                    "id": str(get_uuid_from_seed("c_in_my_const_giver")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("const_giver_module")),
            "function_name": "main",
        },
    ],
    "workflow": {
        "id": str(get_uuid_from_seed("my_workflow")),
        "connections": [
            {
                "input_in_workflow_id": str(get_uuid_from_seed("1001")),
                "input_name": "c",
                "input_id": str(get_uuid_from_seed("input_c_in_1001")),
                "output_in_workflow_id": str(get_uuid_from_seed("1000")),
                "output_name": "x",
                "output_id": str(get_uuid_from_seed("output_c_in_1000")),
            },
            {
                "input_in_workflow_id": str(get_uuid_from_seed("1001")),
                "input_name": "c",
                "input_id": str(get_uuid_from_seed("input_c_in_1001")),
                "output_in_workflow_id": str(get_uuid_from_seed("1000")),
                "output_name": "y",
                "output_id": str(get_uuid_from_seed("output_y_in_1000")),
            },
        ],
        "inputs": [],
        "outputs": [
            {
                "name": "z",
                "id": str(get_uuid_from_seed("output_z_in_1000")),
                "type": "PLOTLYJSON",
                "name_in_subnode": "z",
                "id_of_sub_node": str(get_uuid_from_seed("1000")),
            }
        ],
        "sub_nodes": [
            {
                "id": str(get_uuid_from_seed("1000")),
                "component_uuid": str(get_uuid_from_seed("my_component")),
            },
            {
                "id": str(get_uuid_from_seed("1001")),
                "component_uuid": str(get_uuid_from_seed("my_const_giver")),
            },
        ],
    },
    "configuration": {
        "name": "string",
        "engine": "plain",
        "run_pure_plot_operators": True,
    },
    "workflow_wiring": {
        "input_wirings": [],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    },
}


@pytest.mark.asyncio
async def test_workflow_with_plot_component_and_activated_exec_of_plot_operators(
    async_test_client,
):
    status_code, output = await run_workflow_with_client(
        plot_workflow_json.copy(), async_test_client
    )

    assert status_code == 200

    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"] == {"a": 1.0}


@pytest.mark.asyncio
async def test_workflow_with_plot_component_and_deactivated_exec_of_plot_operators(
    async_test_client,
):
    new_plot_workflow_json = deepcopy(plot_workflow_json)
    new_plot_workflow_json["configuration"] = {
        "name": "string",
        "engine": "plain",
        "run_pure_plot_operators": False,
    }

    status_code, output = await run_workflow_with_client(
        new_plot_workflow_json, async_test_client
    )

    assert status_code == 200

    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"] == {}


@pytest.mark.asyncio
async def test_workflow_with_plot_component_with_non_plot_outputs(async_test_client):
    """Importing a component which is marked as plot component but
    has outputs which are not Plot Outputs should fail
    """
    new_plot_workflow_json = deepcopy(plot_workflow_json)
    new_plot_workflow_json["code_modules"][0][
        "code"
    ] = 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Float, "y": DataType.Float}, outputs={"z": DataType.PlotlyJson, "w": DataType.Float}, is_pure_plot_component=True\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": {"a": 1.0}}'

    status_code, output = await run_workflow_with_client(
        new_plot_workflow_json, async_test_client
    )

    print(output)
    assert status_code == 200

    assert output["result"] == "failure"
    assert "marked as a pure plot component" in output["traceback"]