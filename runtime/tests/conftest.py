from copy import deepcopy
from unittest import mock

import pytest
from httpx import AsyncClient

from hetdesrun.persistence import get_db_engine
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.utils import get_uuid_from_seed
from hetdesrun.webservice.application import init_app


@pytest.fixture(scope="function")
def clean_test_db_engine(use_in_memory_db):
    if use_in_memory_db:
        in_memory_database_url = "sqlite+pysqlite:///:memory:"
        engine = get_db_engine(override_db_url=in_memory_database_url)
    else:
        engine = get_db_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def deactivate_auth():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.auth", False
    ) as _fixture:
        yield _fixture


@pytest.fixture(scope="session")
def app_without_auth(deactivate_auth):
    yield init_app()


def pytest_addoption(parser):
    parser.addoption(
        "--dont-use-in-memory-db",
        action="store_false",
        dest="use_in_memory_db",
        default=True,
    )


@pytest.fixture()
def use_in_memory_db(pytestconfig):
    return pytestconfig.getoption("use_in_memory_db")


@pytest.fixture
def async_test_client(app_without_auth):
    return AsyncClient(app=app_without_auth, base_url="http://test")


@pytest.fixture
async def open_async_test_client(async_test_client):
    async with async_test_client as ac:
        yield ac


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
}


@pytest.fixture
def runtime_execution_base_input_json():
    return deepcopy(base_workflow_json)


@pytest.fixture
def input_json_with_wiring():
    json_with_wiring = deepcopy(base_workflow_json)

    json_with_wiring["workflow_wiring"] = {
        "input_wirings": [],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    }
    return json_with_wiring


@pytest.fixture
def input_json_with_wiring_with_input():
    json_with_wiring = deepcopy(base_workflow_json)

    json_with_wiring["code_modules"][1][
        "code"
    ] = 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\nfrom hetdesrun import logger\n# add your own imports here\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if input/output changes.\n@register(\n    inputs={"inp": DataType.Float}, outputs={"c": DataType.Float}\n)\nasync def main(*, inp):\n    """entrypoint function for this component"""\n    logger.info("TEST")\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    pass\n    return {"c": inp}'

    json_with_wiring["code_modules"][1]["uuid"] = str(
        get_uuid_from_seed("value_giver_module")
    )

    json_with_wiring["components"][1]["inputs"] = [
        {
            "name": "inp",
            "type": "FLOAT",
            "id": str(get_uuid_from_seed("inp_in_my_const_giver")),
        }
    ]

    json_with_wiring["components"][1]["code_module_uuid"] = str(
        str(get_uuid_from_seed("value_giver_module"))
    )

    json_with_wiring["workflow"]["inputs"] = [
        {
            "name": "val_inp",
            "id": str(get_uuid_from_seed("input_inp_in_1001")),
            "type": "FLOAT",
            "name_in_subnode": "inp",
            "id_of_sub_node": str(get_uuid_from_seed("1001")),
        }
    ]

    json_with_wiring["workflow_wiring"] = {
        "input_wirings": [
            {
                "workflow_input_name": "val_inp",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
                "filters": {"value": 32},
            }
        ],
        "output_wirings": [
            {
                "workflow_output_name": "z",
                "adapter_id": 1,
                "ref_id": "TEST-ID",
            }
        ],
    }
    return json_with_wiring
