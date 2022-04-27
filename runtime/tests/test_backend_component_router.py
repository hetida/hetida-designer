from unittest import mock
import pytest

from starlette.testclient import TestClient

from hetdesrun.utils import get_uuid_from_seed

from hetdesrun.webservice.application import app

from hetdesrun.exportimport.importing import load_json

from hetdesrun.persistence import get_db_engine, sessionmaker
from hetdesrun.persistence.dbmodels import Base
from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto

client = TestClient(app)


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


dto_json_component_1 = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "component 1",
    "description": "description of component 1",
    "category": "category",
    "type": "COMPONENT",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": "code",
}
dto_json_component_1_update = {
    "id": str(get_uuid_from_seed("component 1")),
    "groupId": str(get_uuid_from_seed("group of component 1")),
    "name": "new name",
    "description": "description of component 1",
    "category": "Test",
    "type": "COMPONENT",
    "state": "DRAFT",
    "tag": "1.0.0",
    "inputs": [
        {
            "id": str(get_uuid_from_seed("new input")),
            "name": "new_input",
            "type": "INT",
        }
    ],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 1",\n    description="description of component 1",\n    category="category",\n    uuid="c3f0ffdc-ff1c-a612-668c-0a606020ffaa",\n    group_id="b301ff9e-bdbb-8d7c-f6e2-7e83b919a8d3",\n    tag="1.0.0"\n)\ndef main(*, new_input):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}
dto_json_component_2 = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": "code",
}
dto_json_component_2_update = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "RELEASED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 2",\n    description="description of component 2",\n    category="category",\n    uuid="'
    + str(get_uuid_from_seed("component 2"))
    + '",\n    group_id="'
    + str(get_uuid_from_seed("group of component 2"))
    + '",\n    tag="1.0.0"\n)\ndef main(*):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}
dto_json_component_2_deprecate = {
    "id": str(get_uuid_from_seed("component 2")),
    "groupId": str(get_uuid_from_seed("group of component 2")),
    "name": "component 2",
    "description": "description of component 2",
    "category": "category",
    "type": "COMPONENT",
    "state": "DISABLED",
    "tag": "1.0.0",
    "inputs": [],
    "outputs": [],
    "wirings": [],
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n# add your own imports here, e.g.\n#     import pandas as pd\n#     import numpy as np\n\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change."\n@register(\n    inputs={},\n    outputs={},\n    component_name="component 2",\n    description="description of component 2",\n    category="category",\n    uuid="'
    + str(get_uuid_from_seed("component 2"))
    + '",\n    group_id="'
    + str(get_uuid_from_seed("group of component 2"))
    + '",\n    tag="1.0.0"\n)\ndef main(*):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n    # new comment\n    pass\n',
}

dto_json_wiring = {
    "id": "2634db74-157b-4c07-a49d-6aedc6f9a7bc",
    "name": "STANDARD-WIRING",
    "inputWirings": [
        {
            "id": "5021c197-3c38-4e66-b4dc-20e6b5a75bdc",
            "workflowInputName": "new_input",
            "adapterId": "direct_provisioning",
            "filters": {"value": 100},
        },
    ],
    "outputWirings": [],
}

valid_component_dto_dict = {
    "category": "Arithmetic",
    "code": 'from hetdesrun.component.registration import register\nfrom hetdesrun.datatypes import DataType\n\nimport pandas as pd\nimport numpy as np\n\n# ***** DO NOT EDIT LINES BELOW *****\n# These lines may be overwritten if component details or inputs/outputs change.\n@register(\n    inputs={"a": DataType.Any, "b": DataType.Integer},\n    outputs={"modulo": DataType.Any},\n    component_name="Modulo",\n    description="Calculates the modulo to some given b",\n    category="Arithmetic",\n    uuid="ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",\n    group_id="ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",\n    tag="1.0.0"\n)\ndef main(*, a, b):\n    # entrypoint function for this component\n    # ***** DO NOT EDIT LINES ABOVE *****\n    # write your function code here.\n\n    return {"modulo": a % b}\n',
    "description": "Calculates the modulo to some given b",
    "groupId": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "id": "ebb5b2d1-7c25-94dd-ca81-6a9e5b21bc2f",
    "inputs": [
        {
            "id": "1aa579e3-e568-326c-0768-72c725844828",
            "name": "a",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        },
        {
            "id": "6198074e-18fa-0ba1-13a7-8d77b7f2c8f3",
            "name": "b",
            "posX": 0,
            "posY": 0,
            "type": "INT",
        },
    ],
    "name": "Modulo",
    "outputs": [
        {
            "id": "f309d0e5-6f20-2edb-c7be-13f84882af93",
            "name": "modulo",
            "posX": 0,
            "posY": 0,
            "type": "ANY",
        }
    ],
    "state": "RELEASED",
    "tag": "1.0.0",
    "type": "COMPONENT",
    "wirings": [
        {
            "id": "8e7d06f4-1085-4243-bff7-18991d377923",
            "name": "STANDARD-WIRING",
            "inputWirings": [
                {
                    "id": "77886042-28e9-4640-9405-9c3d1d61a08c",
                    "workflowInputName": "a",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": "27"},
                },
                {
                    "id": "f64e6718-2d15-4c1a-828f-65da48fe56a2",
                    "workflowInputName": "b",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": "4"},
                },
            ],
            "outputWirings": [],
        }
    ],
}


@pytest.mark.asyncio
async def test_get_component_revision_by_id_with_valid_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.get(
                "/api/components/" + str(get_uuid_from_seed("component 1"))
            )
        assert response.status_code == 200
        assert response.json() == dto_json_component_1


@pytest.mark.asyncio
async def test_get_component_revision_by_id_with_inexistent_component(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.get(
                "/api/components/" + str(get_uuid_from_seed("inexistent component"))
            )
        assert response.status_code == 404
        assert "Found no" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.post("/api/components/", json=dto_json_component_1)

        assert response.status_code == 201
        assert response.json()["name"] == dto_json_component_1["name"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
                json=dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )
        print(response.json()["code"])
        assert "new_input" in response.json()["code"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_non_existing_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
                json=dto_json_component_1_update,
            )

        assert response.status_code == 201
        assert response.json()["name"] == "new name"
        assert response.json()["category"] == "Test"
        assert response.json()["inputs"][0]["id"] == str(
            get_uuid_from_seed("new input")
        )
        assert "new comment" in response.json()["code"]
        assert "revision_group_id" in response.json()["code"]


@pytest.mark.asyncio
async def test_update_transformation_revision_from_released_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 2")),
                json=dto_json_component_2_update,
            )

        assert response.status_code == 403


@pytest.mark.asyncio
async def test_deprecate_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_2
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.put(
                "/api/components/" + str(get_uuid_from_seed("component 2")),
                json=dto_json_component_2_deprecate,
            )

        assert response.status_code == 201
        assert response.json()["state"] == "DISABLED"
        assert response.json()["name"] != "new name"
        assert response.json()["category"] != "Test"
        assert len(response.json()["inputs"]) == 0
        assert "new comment" not in response.json()["code"]


@pytest.mark.asyncio
async def test_delete_transformation_revision_from_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.delete(
                "/api/components/" + str(get_uuid_from_seed("component 1")),
            )

        assert response.status_code == 204


@pytest.mark.asyncio
async def test_set_test_wiring_for_component_dto(
    async_test_client, clean_test_db_engine
):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **dto_json_component_1_update
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/"
                + str(get_uuid_from_seed("component 1"))
                + "/wirings",
                json=dto_json_wiring,
            )

        assert response.status_code == 200


@pytest.mark.asyncio
async def test_execute_for_component_dto(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        store_single_transformation_revision(
            ComponentRevisionFrontendDto(
                **valid_component_dto_dict
            ).to_transformation_revision()
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/" + valid_component_dto_dict["id"] + "/execute",
                json=valid_component_dto_dict["wirings"][0],
            )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()


@pytest.mark.asyncio
async def test_execute_for_component_without_hetdesrun_imports(async_test_client, clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):

        path = "./transformations/components/anomaly-detection/isolation-forest_100_cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354.json"
        component_tr_json = load_json(path)
        wiring_json = {
            "id":"cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354",
            "name":"STANDARD-WIRING",
            "inputWirings":[
                {
                    "id":"e583535f-3452-434d-9a41-8ffa476e271f",
                    "workflowInputName":"n_estimators",
                    "adapterId":"direct_provisioning",
                    "filters":{"value":"100"}
                },
                {
                    "id":"2ac9a1bc-2235-4bf6-bb11-c2423d3bf979",
                    "workflowInputName":"test_data",
                    "adapterId":"direct_provisioning",
                    "filters":{"value":"{\n        \"0\": 1.4926660699,\n        \"1\": 1.4486349492,\n        \"2\": 1.5450470794,\n        \"3\": 1.776656204,\n        \"4\": 1.2505807659,\n        \"5\": 1.6015711927,\n        \"6\": 1.6289885968,\n        \"7\": 1.3396458715,\n        \"8\": 1.584027853,\n        \"9\": 1.5086498128,\n        \"10\": 1.3082738461,\n        \"11\": 1.3551707245,\n        \"12\": 1.3047677269,\n        \"13\": 1.1957268597,\n        \"14\": 1.589771313,\n        \"15\": 1.4559757939,\n        \"16\": 1.5915332444,\n        \"17\": 1.0671794303,\n        \"18\": 1.432818479,\n        \"19\": 1.4300797641,\n        \"20\": 1.3715935639,\n        \"21\": 1.3572668951,\n        \"22\": 1.0734477529,\n        \"23\": 1.3622193297,\n        \"24\": 1.4287684992,\n        \"25\": 1.2215251242,\n        \"26\": 1.3652527468,\n        \"27\": 1.1973235753,\n        \"28\": 1.7253995801,\n        \"29\": 1.2580476039,\n        \"30\": 1.0545478427,\n        \"31\": 1.0117721362,\n        \"32\": 1.1578791663,\n        \"33\": 1.4706967921,\n        \"34\": 1.5886736947,\n        \"35\": 1.1851616194,\n        \"36\": 1.2706084302,\n        \"37\": 1.22543923,\n        \"38\": 1.7309807976,\n        \"39\": 1.5866646984,\n        \"40\": 1.5077532977,\n        \"41\": 1.4359288381,\n        \"42\": 1.7056115478,\n        \"43\": 1.0703683588,\n        \"44\": 1.2913088978,\n        \"45\": 1.6538359777,\n        \"46\": 1.4408159436,\n        \"47\": 1.1711791235,\n        \"48\": 1.5256179052,\n        \"49\": 1.3187467931,\n        \"50\": 1.1115703,\n        \"51\": 1.4046511263,\n        \"52\": 1.4403180152,\n        \"53\": 1.5672974594,\n        \"54\": 1.1779609522,\n        \"55\": 1.5797056641,\n        \"56\": 1.4524569179,\n        \"57\": 1.4070450575,\n        \"58\": 1.5290660426,\n        \"59\": 1.3120717628,\n        \"60\": 1.3453596376,\n        \"61\": 1.2316969297,\n        \"62\": 1.6378821897,\n        \"63\": 1.2760642118,\n        \"64\": 1.4956937624,\n        \"65\": 1.4929910048,\n        \"66\": 1.3738941343,\n        \"67\": 1.5852288325,\n        \"68\": 0.9717649741,\n        \"69\": 1.6427129664,\n        \"70\": 1.2175972616,\n        \"71\": 1.2979690188,\n        \"72\": 1.7029654725,\n        \"73\": 1.378315634,\n        \"74\": 1.4904271716,\n        \"75\": 1.5066028189,\n        \"76\": 1.3945879926,\n        \"77\": 1.4913153696,\n        \"78\": 1.4618294119,\n        \"79\": 1.1675132196,\n        \"80\": 1.2606787057,\n        \"81\": 1.6244382896,\n        \"82\": 1.6646727012,\n        \"83\": 1.4031978084,\n        \"84\": 1.5277458348,\n        \"85\": 1.3607462888,\n        \"86\": 1.129613468,\n        \"87\": 1.2690961303,\n        \"88\": 1.3087356812,\n        \"89\": 1.3779695334,\n        \"90\": 1.6356347978,\n        \"91\": 1.45676668,\n        \"92\": 1.4339967622,\n        \"93\": 1.5791665539,\n        \"94\": 1.4127552469,\n        \"95\": 1.5778551374,\n        \"96\": 1.4546758127,\n        \"97\": 1.1843789384,\n        \"98\": 1.4510047706,\n        \"99\": 1.2788758327,\n        \"100\": 0.3750956282,\n        \"101\": -0.348332961,\n        \"102\": 1.1273700108,\n        \"103\": -0.5828114497,\n        \"104\": -0.6019201001,\n        \"105\": 0.1459754345,\n        \"106\": 0.4926503544,\n        \"107\": 0.2154680857,\n        \"108\": -0.2551963406,\n        \"109\": -0.0021394574,\n        \"110\": 0.803016169,\n        \"111\": -0.3932162493,\n        \"112\": 0.0443088352,\n        \"113\": 0.7563416189,\n        \"114\": 0.2806832923,\n        \"115\": -0.0820868678,\n        \"116\": 0.6539103775,\n        \"117\": 0.6807191115,\n        \"118\": 0.6344428224,\n        \"119\": 0.6345290121,\n        \"120\": 0.2538398248,\n        \"121\": 0.0901253052,\n        \"122\": 0.5408800137,\n        \"123\": -0.3640374072,\n        \"124\": 0.2546865562,\n        \"125\": -0.7150082477,\n        \"126\": -0.2621021415,\n        \"127\": -0.3699787618,\n        \"128\": 0.0209162847,\n        \"129\": -0.2729625202,\n        \"130\": 0.416004053,\n        \"131\": -0.2833210194,\n        \"132\": 0.0460272259,\n        \"133\": 0.4255764332,\n        \"134\": 0.0752196307,\n        \"135\": -0.1529583948,\n        \"136\": 0.4238010375,\n        \"137\": 0.0456235429,\n        \"138\": 0.0527215759,\n        \"139\": 0.6908365451,\n        \"140\": -0.2992636577,\n        \"141\": 0.0731327305,\n        \"142\": -0.4644478508,\n        \"143\": 0.1617790151,\n        \"144\": 0.3986000441,\n        \"145\": -0.4138682181,\n        \"146\": 0.0309860526,\n        \"147\": 0.1825449262,\n        \"148\": 0.5308633933,\n        \"149\": 0.590488114\n    }"}
                },
                {
                    "id":"800a3795-4ed2-4d9c-afc8-565155406538",
                    "workflowInputName":"train_data",
                    "adapterId":"direct_provisioning",
                    "filters":{"value":"{\n        \"0\": 2.0918517167,\n        \"1\": 1.6351422204,\n        \"2\": 1.8909793726,\n        \"3\": 2.4315905044,\n        \"4\": 1.2556615935,\n        \"5\": 2.5702117298,\n        \"6\": 1.828156926,\n        \"7\": 1.6570902517,\n        \"8\": 1.7755659202,\n        \"9\": 2.0584771141,\n        \"10\": 1.1923644451,\n        \"11\": 1.3875187648,\n        \"12\": 1.336018039,\n        \"13\": 1.1558574253,\n        \"14\": 1.9366961319,\n        \"15\": 2.209024992,\n        \"16\": 1.1838732985,\n        \"17\": 0.6707142277,\n        \"18\": 1.7757872413,\n        \"19\": 1.2597629314,\n        \"20\": 1.2592926437,\n        \"21\": 1.591255678,\n        \"22\": 1.1741298861,\n        \"23\": 2.0834988691,\n        \"24\": 1.7448564658,\n        \"25\": 1.0509356347,\n        \"26\": 1.5073314682,\n        \"27\": 1.4379901604,\n        \"28\": 2.2565441397,\n        \"29\": 1.404213351,\n        \"30\": 1.3046580437,\n        \"31\": 0.9435742958,\n        \"32\": 0.7083373529,\n        \"33\": 1.4271506958,\n        \"34\": 1.9626931721,\n        \"35\": 1.2600086319,\n        \"36\": 1.6062375805,\n        \"37\": 1.2602345519,\n        \"38\": 2.2832867901,\n        \"39\": 1.719515212,\n        \"40\": 2.1791558553,\n        \"41\": 1.7018714812,\n        \"42\": 2.0943046384,\n        \"43\": 0.8383702568,\n        \"44\": 1.404694486,\n        \"45\": 2.3567742096,\n        \"46\": 1.6611731096,\n        \"47\": 1.3664794499,\n        \"48\": 1.6608608073,\n        \"49\": 1.8016440495,\n        \"50\": 1.1962660333,\n        \"51\": 2.0264224151,\n        \"52\": 2.0660797791,\n        \"53\": 1.6572699065,\n        \"54\": 1.0201013999,\n        \"55\": 1.5964380435,\n        \"56\": 1.6433887725,\n        \"57\": 1.7935542862,\n        \"58\": 2.5341105696,\n        \"59\": 1.5681698292,\n        \"60\": 1.4832137965,\n        \"61\": 0.6673825046,\n        \"62\": 2.3298901288,\n        \"63\": 1.3736537956,\n        \"64\": 1.5270363292,\n        \"65\": 2.4747877069,\n        \"66\": 1.0965899798,\n        \"67\": 1.8645734583,\n        \"68\": 0.4106281559,\n        \"69\": 2.3566780324,\n        \"70\": 1.2541726056,\n        \"71\": 1.4265057174,\n        \"72\": 2.4797764864,\n        \"73\": 1.8623157346,\n        \"74\": 1.5631520074,\n        \"75\": 1.6730918717,\n        \"76\": 1.3830289178,\n        \"77\": 2.2563192073,\n        \"78\": 1.4696583766,\n        \"79\": 0.7304943724,\n        \"80\": 1.3529801574,\n        \"81\": 1.5027970746,\n        \"82\": 2.3460010761,\n        \"83\": 1.6457706798,\n        \"84\": 2.0197152222,\n        \"85\": 1.4053767672,\n        \"86\": 1.0640404861,\n        \"87\": 1.3456315961,\n        \"88\": 1.8790157397,\n        \"89\": 1.5337356542,\n        \"90\": 2.0890407511,\n        \"91\": 1.6456890051,\n        \"92\": 1.750703967,\n        \"93\": 1.4062853135,\n        \"94\": 1.5986223975,\n        \"95\": 2.1774012998,\n        \"96\": 1.7434766038,\n        \"97\": 1.2101237951,\n        \"98\": 1.7539782233,\n        \"99\": 0.8933229057,\n        \"100\": 0.2474688349,\n        \"101\": 0.1110004675,\n        \"102\": 0.0282859274,\n        \"103\": 0.1169015529,\n        \"104\": 0.0873378628,\n        \"105\": 0.1788892937,\n        \"106\": 0.184303781,\n        \"107\": 0.0747153259,\n        \"108\": 0.2769387623,\n        \"109\": -0.0900818405,\n        \"110\": 0.0733949175,\n        \"111\": 0.2833456832,\n        \"112\": 0.0083655977,\n        \"113\": 0.3372043953,\n        \"114\": 0.2285817183,\n        \"115\": 0.0082504206,\n        \"116\": 0.307490622,\n        \"117\": 0.1145009276,\n        \"118\": 0.2019423307,\n        \"119\": 0.0008354562,\n        \"120\": -0.1130743973,\n        \"121\": -0.2473543353,\n        \"122\": -0.0006302528,\n        \"123\": 0.0851482521,\n        \"124\": 0.293301912,\n        \"125\": 0.4601618525,\n        \"126\": 0.0843088936,\n        \"127\": 0.6793118898,\n        \"128\": -0.1196668846,\n        \"129\": -0.1463627937,\n        \"130\": 0.2511802345,\n        \"131\": -0.3425442505,\n        \"132\": 0.0120582876,\n        \"133\": -0.0022185432,\n        \"134\": 0.1041517971,\n        \"135\": 0.313957358,\n        \"136\": 0.1407613516,\n        \"137\": 0.2622005096,\n        \"138\": 0.1660724099,\n        \"139\": 0.0878323083,\n        \"140\": 0.0292133339,\n        \"141\": -0.2577132774,\n        \"142\": -0.049417556,\n        \"143\": -0.0827495615,\n        \"144\": 0.198339056,\n        \"145\": -0.0708022007,\n        \"146\": 0.1692034915,\n        \"147\": 0.1987969782,\n        \"148\": 0.1007444086,\n        \"149\": 0.1225206078\n}"}
                }
            ],
            "outputWirings":[]
        }

        store_single_transformation_revision(
            TransformationRevision(**component_tr_json)
        )

        async with async_test_client as ac:
            response = await ac.post(
                "/api/components/" + component_tr_json["id"] + "/execute",
                json=wiring_json,
            )

        assert response.status_code == 200
        assert "output_types_by_output_name" in response.json()
