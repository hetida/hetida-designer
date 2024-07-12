from copy import deepcopy
from typing import Any

import pytest
from httpx import AsyncClient

from hetdesrun.utils import get_uuid_from_seed


@pytest.mark.asyncio
async def test_swagger_ui_available(async_test_client: AsyncClient) -> None:
    async with async_test_client as ac:
        response = await ac.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


@pytest.mark.asyncio
async def test_access_api_endpoint(async_test_client: AsyncClient) -> None:
    async with async_test_client as ac:
        response = await ac.get("engine/info")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio
async def test_access_api_endpoint_with_trailing_slash(
    async_test_client: AsyncClient,
) -> None:
    async with async_test_client as ac:
        response = await ac.get("engine/info/")
    assert response.status_code == 200
    assert "version" in response.json()


base_workflow_json: dict = {
    "code_modules": [
        {  # ordinary function entry point
            "uuid": str(get_uuid_from_seed("my_code_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Float, "y": DataType.Float}, outputs={"z": DataType.Float}\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": x+y}',  # noqa: E501
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Float}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": 2.0}',  # noqa: E501
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "tag": "1.0.0",
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
            "tag": "1.0.0",
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
        "tr_id": "tr_id",
        "tr_name": "tr_name",
        "tr_tag": "1.0.0",
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
    "trafo_id": str(get_uuid_from_seed("my_workflow")),
}


async def run_workflow_with_client(
    workflow_json: dict, open_async_test_client: AsyncClient
) -> tuple[int, Any]:
    async with open_async_test_client as ac:
        response = await ac.post("engine/runtime", json=workflow_json)
    return response.status_code, response.json()


@pytest.mark.asyncio
async def test_running_workflow(async_test_client: AsyncClient) -> None:
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
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nimport logging\ntest_logger = logging.getLogger(__name__)\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"x": DataType.Series, "y": DataType.Float}, outputs={"z": DataType.DataFrame}\n)\ndef main(*, x, y):\n    """entrypoint function for this component"""\n    test_logger.info("TEST in component function " + __name__)\n    # print(1 / 0)\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"z": x.to_frame() + y}',  # noqa: E501
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Float}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": 2.0}',  # noqa: E501
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "tag": "1.0.0",
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
            "tag": "1.0.0",
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
        "tr_id": "tr_id",
        "tr_name": "tr_name",
        "tr_tag": "1.0.0",
    },
    "configuration": {"name": "string", "engine": "plain"},
    "workflow_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "x",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": "[1.0, 2.0, 3.5]"},
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
    "trafo_id": str(get_uuid_from_seed("my_workflow")),
}


@pytest.mark.asyncio
async def test_workflow_with_series_input_and_dataframe_output(
    async_test_client: AsyncClient,
) -> None:
    status_code, output = await run_workflow_with_client(
        series_input_workflow_json.copy(), async_test_client
    )

    assert status_code == 200
    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"]["__data__"]["0"] == {
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
            "tag": "1.0.0",
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
        "tr_id": "tr_id",
        "tr_name": "tr_name",
        "tr_tag": "1.0.0",
    },
    "configuration": {"name": "string", "engine": "plain"},
    "workflow_wiring": {
        "input_wirings": [
            {
                "workflow_input_name": "x",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": '{"a": [1.0, 2.0, 3.5]}'},
            },
            {
                "workflow_input_name": "y",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": "2.0"},
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
    "trafo_id": str(get_uuid_from_seed("my_workflow")),
}


@pytest.mark.asyncio
async def test_single_node_workflow_with_dataframe_input_and_series_output(
    async_test_client: AsyncClient,
) -> None:
    status_code, output = await run_workflow_with_client(
        single_node_input_workflow_json.copy(), async_test_client
    )

    assert status_code == 200

    assert output["result"] == "ok"
    assert output["output_results_by_output_name"]["z"]["__data__"]["data"] == [
        3.0,
        4.0,
        5.5,
    ]
    assert output["output_results_by_output_name"]["z"]["__data__"]["index"] == [
        0,
        1,
        2,
    ]


plot_workflow_json = {
    "code_modules": [
        {  # ordinary function entry point
            "uuid": str(get_uuid_from_seed("my_code_module")),
            "code": (
                "from hetdesrun.component.registration import register\n"
                "from hetdesrun.datatypes import DataType  # add your own imports here\n"
                "from hdutils import plotly_fig_to_json_dict\n\n"
                "import pandas as pd\n\nfrom plotly.graph_objects import Figure\n"
                "import plotly.express as px\n\nimport plotly.io as pio\n\n"
                "pio.templates.default = None\n\n\ndef timeseries_comparison_plot(\n"
                "    x: pd.Series,\n    y: pd.Series,\n"
                "    traces_opts: dict = {},\n    layout_opts: dict = {\n"
                '        "xaxis_title": "Time",\n        "yaxis_title": "Values",\n'
                '        "autosize": True,\n        "height": 200,\n'
                "    },\n    line_opts: dict = {},\n) -> Figure:\n"
                '    """Create a single time series line plot Plotly figure\n    \n'
                '    Returns the plotly figure object.\n    """\n\n    fig = Figure()\n'
                "    # Only thing I figured is - I could do this\n\n    s1 = x.sort_index()\n\n"
                "    fig.add_scatter(\n"
                '        x=s1.index, y=s1, mode="lines", name=s1.name if s1.name else "x"\n'
                "    )  # Not what is desired - need a line\n\n    s2 = y.sort_index()\n\n"
                "    fig.add_scatter(\n"
                '        x=s2.index, y=s2, mode="lines", name=s2.name if s2.name else "y"\n'
                "    )  # Not what is desired - need a line\n\n"
                "    fig.update_layout(**layout_opts)\n"
                "    fig.update_traces(traces_opts)  # set line color?\n\n"
                "    fig.update_layout(margin=dict(l=0, r=0, b=0, t=5, pad=0))\n\n"
                "    fig.update_yaxes(automargin=True)\n    fig.update_xaxes(automargin=True)\n"
                "    return fig\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n"
                "# These lines may be overwritten if component details or inputs/outputs change.\n"
                'COMPONENT_INFO = {\n    "inputs": {\n        "x": "SERIES",\n'
                '        "y": "SERIES",\n    },\n    "outputs": {\n'
                '        "comparison_plot": "PLOTLYJSON",\n    },\n'
                '    "name": "Compare Two Timeseries Plot",\n    "category": "Visualization",\n'
                '    "description": "Plotting of two timeseries in the same plot",\n'
                '    "version_tag": "1.0.0",\n    "id": "a432923f-4718-44ae-3c9c-9832e68724bb",\n'
                '    "revision_group_id": "a432923f-4718-44ae-3c9c-9832e68724bb",\n'
                '    "state": "RELEASED",\n'
                '    "released_timestamp": "2022-02-09T17:33:30.020807+00:00",\n}\n\n\n'
                "def main(*, x, y):\n    # entrypoint function for this component\n"
                "    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n"
                '    return {\n        "comparison_plot": plotly_fig_to_json_dict(\n'
                "            timeseries_comparison_plot(x, y)\n        )\n    }\n"
            ),
        },
        {  # async def entrypoint
            "uuid": str(get_uuid_from_seed("const_giver_module")),
            "code": 'import pandas as pd\nfrom hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={}, outputs={"c": DataType.Series}\n)\nasync def main():\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    return {"c": pd.Series([42.2, 18.7, 25.9])}',  # noqa: E501
        },
    ],
    "components": [
        {
            "uuid": str(get_uuid_from_seed("my_component")),
            "tag": "1.0.0",
            "inputs": [
                {
                    "name": "x",
                    "type": "SERIES",
                    "id": str(get_uuid_from_seed("x_in_my_component")),
                },
                {
                    "name": "y",
                    "type": "SERIES",
                    "id": str(get_uuid_from_seed("y_in_my_component")),
                },
            ],
            "outputs": [
                {
                    "name": "comparison_plot",
                    "type": "PLOTLYJSON",
                    "id": str(get_uuid_from_seed("z_in_my_component")),
                }
            ],
            "code_module_uuid": str(get_uuid_from_seed("my_code_module")),
            "function_name": "main",
        },
        {
            "uuid": str(get_uuid_from_seed("my_const_giver")),
            "tag": "1.0.0",
            "inputs": [],
            "outputs": [
                {
                    "name": "c",
                    "type": "SERIES",
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
                "name_in_subnode": "comparison_plot",
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
        "tr_id": "tr_id",
        "tr_name": "tr_name",
        "tr_tag": "1.0.0",
    },
    "configuration": {
        "name": "string",
        "engine": "plain",
        "run_pure_plot_operators": True,
    },
    "workflow_wiring": {
        "input_wirings": [],
        "output_wirings": [{"adapter_id": 1, "workflow_output_name": "z"}],
    },
    "trafo_id": str(get_uuid_from_seed("my_workflow")),
}


@pytest.mark.asyncio
async def test_workflow_with_plot_component_and_activated_exec_of_plot_operators(
    async_test_client: AsyncClient,
) -> None:
    status_code, output = await run_workflow_with_client(
        plot_workflow_json.copy(), async_test_client
    )

    assert status_code == 200

    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"] == {
        "data": [
            {
                "mode": "lines",
                "name": "x",
                "x": [0, 1, 2],
                "y": [42.2, 18.7, 25.9],
                "type": "scatter",
            },
            {
                "mode": "lines",
                "name": "y",
                "x": [0, 1, 2],
                "y": [42.2, 18.7, 25.9],
                "type": "scatter",
            },
        ],
        "layout": {
            "xaxis": {"title": {"text": "Time"}, "automargin": True},
            "yaxis": {"title": {"text": "Values"}, "automargin": True},
            "autosize": True,
            "height": 200,
            "margin": {"l": 0, "r": 0, "b": 0, "t": 5, "pad": 0},
        },
    }


@pytest.mark.asyncio
async def test_workflow_with_plot_component_and_deactivated_exec_of_plot_operators(
    async_test_client: AsyncClient,
) -> None:
    new_plot_workflow_json = deepcopy(plot_workflow_json)
    new_plot_workflow_json["configuration"] = {
        "name": "string",
        "engine": "plain",
        "run_pure_plot_operators": False,
    }

    status_code, output = await run_workflow_with_client(new_plot_workflow_json, async_test_client)

    assert status_code == 200

    assert output["result"] == "ok"

    assert output["output_results_by_output_name"]["z"] == {}
