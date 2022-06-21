from copy import deepcopy
from uuid import UUID

import pytest

from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.backend.models.wiring import InputWiringFrontendDto, WiringFrontendDto
from hetdesrun.backend.models.workflow import (
    WorkflowIoFrontendDto,
    WorkflowLinkFrontendDto,
    WorkflowOperatorFrontendDto,
    WorkflowRevisionFrontendDto,
    get_operator_and_connector_name,
    position_from_input_connector_id,
)

# pylint: disable=too-many-lines

valid_workflow_example_iso_forest: dict = {
    "id": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
    "groupId": "b123bfb6-f8ee-422f-bbf8-01668a471e88",
    "name": "Iso Forest Example",
    "description": "Example of a simple Isolation Forest application",
    "category": "Examples",
    "type": "WORKFLOW",
    "state": "RELEASED",
    "tag": "1.0.0",
    "operators": [
        # 0
        {
            "id": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
            "groupId": "a4064897-66d3-9601-328e-5ae9036665c5",
            "name": "Name Series",
            "description": "Give a name to a series",
            "category": "Connectors",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "a4064897-66d3-9601-328e-5ae9036665c5",
            "inputs": [
                {
                    "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                    "type": "SERIES",
                    "name": "input",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                    "type": "STRING",
                    "name": "name",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                    "type": "SERIES",
                    "name": "output",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "posY": 310,
            "posX": 170,
        },
        # 1
        {
            "id": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "groupId": "096c6181-4ba5-0ee7-361a-3c32eee8c0c2",
            "name": "2D Grid Generator",
            "description": "Generates 2 dimensional grids",
            "category": "Visualization",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "096c6181-4ba5-0ee7-361a-3c32eee8c0c2",
            "inputs": [
                {
                    "id": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
                    "type": "INT",
                    "name": "n",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "02a7f8f6-0fb5-5a65-12d7-a21d61cdd271",
                    "type": "FLOAT",
                    "name": "x_max",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "4ef2610a-4321-004c-aee8-5cbf87ac1a49",
                    "type": "FLOAT",
                    "name": "x_min",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "80fb9d9d-d926-8cb6-6a41-777ba806f6ea",
                    "type": "FLOAT",
                    "name": "y_max",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "b3492592-b3e8-caaa-a4d4-4670d110d7f0",
                    "type": "FLOAT",
                    "name": "y_min",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "474c27a3-df58-7b9f-ff7e-d57a2e416fb9",
                    "type": "SERIES",
                    "name": "x_indices",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "597905f3-db79-f46b-db04-dc22cdadf449",
                    "type": "SERIES",
                    "name": "x_values",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "0e368818-fdfb-6796-a463-8bd9d5ff03e5",
                    "type": "SERIES",
                    "name": "y_indices",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "38be3a38-8761-fc80-cab0-da2c12f4a9c8",
                    "type": "SERIES",
                    "name": "y_values",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "posY": 30,
            "posX": 160,
        },
        # 2
        {
            "id": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "groupId": "cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354",
            "name": "Isolation Forest",
            "description": "A Isolation Forest Model",
            "category": "Anomaly Detection",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354",
            "inputs": [
                {
                    "id": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
                    "type": "INT",
                    "name": "n_estimators",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "bc5ae666-e1fb-9189-8f72-d681eb5dcfde",
                    "type": "DATAFRAME",
                    "name": "test_data",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "017e5542-46dd-e1aa-d6f8-4026dcad3d44",
                    "type": "DATAFRAME",
                    "name": "train_data",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "4594161b-f878-09c3-ab66-c1803728ea62",
                    "type": "SERIES",
                    "name": "decision_function_values",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "68234ebe-51c0-96b9-c95b-86548f09e79c",
                    "type": "ANY",
                    "name": "trained_model",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "posY": 180,
            "posX": 1190,
        },
        # 3
        {
            "id": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
            "groupId": "0d08af64-3f34-cddc-354b-d6a26c3f1aab",
            "name": "Combine as named column into DataFrame",
            "description": "Combine as named column into a DataFrame.",
            "category": "Connectors",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "0d08af64-3f34-cddc-354b-d6a26c3f1aab",
            "inputs": [
                {
                    "id": "fc417e48-f7d8-0bbf-60ac-af92a9150170",
                    "type": "STRING",
                    "name": "column_name",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab",
                    "type": "SERIES",
                    "name": "series",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
                    "type": "ANY",
                    "name": "series_or_dataframe",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "2bad1916-9d38-2409-b236-ebfce1fc1fae",
                    "type": "DATAFRAME",
                    "name": "dataframe",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "posY": 280,
            "posX": 705,
        },
        # 4
        {
            "id": "177db51b-6a68-4808-8e09-1a6d87f3e579",
            "groupId": "a4064897-66d3-9601-328e-5ae9036665c5",
            "name": "Name Series (2)",
            "description": "Give a name to a series",
            "category": "Connectors",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "a4064897-66d3-9601-328e-5ae9036665c5",
            "inputs": [
                {
                    "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                    "type": "SERIES",
                    "name": "input",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                    "type": "STRING",
                    "name": "name",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                    "type": "SERIES",
                    "name": "output",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "posY": 460,
            "posX": 175,
        },
        # 5
        {
            "id": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
            "groupId": "68f91351-a1f5-9959-414a-2c72003f3226",
            "name": "Combine into DataFrame",
            "description": "Combine data into a DataFrame",
            "category": "Connectors",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "68f91351-a1f5-9959-414a-2c72003f3226",
            "inputs": [
                {
                    "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                    "type": "SERIES",
                    "name": "series",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                    "type": "ANY",
                    "name": "series_or_dataframe",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                    "type": "DATAFRAME",
                    "name": "dataframe",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "posY": 120,
            "posX": 700,
        },
        # 6
        {
            "id": "4983a39a-88c8-4683-a79d-9321eabe30eb",
            "groupId": "d1fb4ae5-ef27-26b8-7a58-40b7cd8412e7",
            "name": "Forget",
            "description": "Throw away the input",
            "category": "Connectors",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "d1fb4ae5-ef27-26b8-7a58-40b7cd8412e7",
            "inputs": [
                {
                    "id": "b7803aec-db20-6bea-970f-0566ded49a7c",
                    "type": "ANY",
                    "name": "input",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "outputs": [],
            "posY": 210,
            "posX": 1610,
        },
        # 7
        {
            "id": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "groupId": "f7530499-51b2-dd01-0d21-c24ee6f8c37e",
            "name": "Contour Plot",
            "description": "A simple contour plot",
            "category": "Visualization",
            "type": "COMPONENT",
            "state": "RELEASED",
            "tag": "1.0.0",
            "itemId": "f7530499-51b2-dd01-0d21-c24ee6f8c37e",
            "inputs": [
                {
                    "id": "829cbd05-7a33-c931-b16e-a105f9a7c885",
                    "type": "SERIES",
                    "name": "x",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "54e9008c-0451-9e1c-c334-31e3887a4b07",
                    "type": "SERIES",
                    "name": "y",
                    "posY": 0,
                    "posX": 0,
                },
                {
                    "id": "455f7a00-c731-b2ba-ee84-8d8b567bd50e",
                    "type": "SERIES",
                    "name": "z",
                    "posY": 0,
                    "posX": 0,
                },
            ],
            "outputs": [
                {
                    "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
                    "type": "PLOTLYJSON",
                    "name": "contour_plot",
                    "posY": 0,
                    "posX": 0,
                }
            ],
            "posY": -160,
            "posX": 1610,
        },
    ],
    "links": [
        # 0
        {
            "id": "4497b894-dba0-4555-8b63-eb2b993c7592",
            "fromOperator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
            "fromConnector": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
            "toOperator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
            "toConnector": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
            "path": [],
        },
        # 1
        {
            "id": "e9fa0523-dfc8-4c47-ab9b-7ac64eff87ea",
            "fromOperator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
            "fromConnector": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
            "toOperator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
            "toConnector": "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab",
            "path": [],
        },
        # 2
        {
            "id": "8bf65f5f-7267-4ace-b137-2ba57500c4df",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "196c78f4-6b9a-4476-9b37-ec80986a6a47",
            "toOperator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
            "toConnector": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
            "path": [],
        },
        # 3
        {
            "id": "2f1644a8-6638-4c54-a343-6300f001d693",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "1c3224e0-90e6-4d03-9160-3a9417c27841",
            "toOperator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
            "toConnector": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
            "path": [],
        },
        # 4
        {
            "id": "0f52855d-a57b-4ac5-a5f8-db3eadb51240",
            "fromOperator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "fromConnector": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
            "toOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "toConnector": "5dcdf141-590f-42d6-86bd-460af86147a7",
            "path": [],
        },
        # 5
        {
            "id": "4281ddc6-af44-4e72-bbdc-f2a7e9cef9fc",
            "fromOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "fromConnector": "597905f3-db79-f46b-db04-dc22cdadf449",
            "toOperator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
            "toConnector": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
            "path": [],
        },
        # 6
        {
            "id": "0f2c8fd5-2032-4f0a-9bb7-39054ae7e4c5",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
            "toOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "toConnector": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
            "path": [],
        },
        # 7
        {
            "id": "deb0c00b-88c7-4930-8c22-12d18c395fdd",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "f468e81c-0e8f-4869-a268-892a391327d6",
            "toOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "toConnector": "02a7f8f6-0fb5-5a65-12d7-a21d61cdd271",
            "path": [],
        },
        # 8
        {
            "id": "978a06f2-1e4c-4df2-bbb6-e3e7bbd43929",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "d5c0c6b6-3b9d-48ed-9c40-70ecf14a3d0d",
            "toOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "toConnector": "4ef2610a-4321-004c-aee8-5cbf87ac1a49",
            "path": [],
        },
        # 9
        {
            "id": "89c5c8fb-dad1-402e-9ad9-787ab19b762b",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "1cabf944-d63e-4d0d-a1e7-d6c0ffb193c5",
            "toOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "toConnector": "80fb9d9d-d926-8cb6-6a41-777ba806f6ea",
            "path": [],
        },
        # 10
        {
            "id": "81604791-271e-4c79-9f08-19cbf260d39f",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "2c212317-15a7-4599-b1f2-b6333a6c7a2b",
            "toOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "toConnector": "b3492592-b3e8-caaa-a4d4-4670d110d7f0",
            "path": [],
        },
        # 11
        {
            "id": "54162076-43a3-4ac1-ab30-9854b5a1ac0b",
            "fromOperator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "fromConnector": "4594161b-f878-09c3-ab66-c1803728ea62",
            "toOperator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "toConnector": "455f7a00-c731-b2ba-ee84-8d8b567bd50e",
            "path": [],
        },
        # 12
        {
            "id": "fb64fdd5-d9b2-4e73-a480-3436d150d49f",
            "fromOperator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "fromConnector": "68234ebe-51c0-96b9-c95b-86548f09e79c",
            "toOperator": "4983a39a-88c8-4683-a79d-9321eabe30eb",
            "toConnector": "b7803aec-db20-6bea-970f-0566ded49a7c",
            "path": [],
        },
        # 13
        {
            "id": "dc00bb92-a52e-4a8a-a91c-6c88cd85f9f1",
            "fromOperator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
            "fromConnector": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
            "toOperator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "toConnector": "bc5ae666-e1fb-9189-8f72-d681eb5dcfde",
            "path": [],
        },
        # 14
        {
            "id": "23fc5984-daf8-482b-859b-3a8eef53f0ce",
            "fromOperator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
            "fromConnector": "2bad1916-9d38-2409-b236-ebfce1fc1fae",
            "toOperator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "toConnector": "017e5542-46dd-e1aa-d6f8-4026dcad3d44",
            "path": [],
        },
        # 15
        {
            "id": "a8afb568-965a-4ea0-aaa6-bb23dd373ed5",
            "fromOperator": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
            "fromConnector": "8a569d4a-863a-4800-abb5-819cc1e8a030",
            "toOperator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "toConnector": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
            "path": [],
        },
        # 16
        {
            "id": "4001126b-12d1-4879-b911-f5dcd60c9aca",
            "fromOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "fromConnector": "38be3a38-8761-fc80-cab0-da2c12f4a9c8",
            "toOperator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
            "toConnector": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
            "path": [],
        },
        # 17
        {
            "id": "8ca7a384-d0eb-4871-8022-6097bd5dce0c",
            "fromOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "fromConnector": "474c27a3-df58-7b9f-ff7e-d57a2e416fb9",
            "toOperator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "toConnector": "829cbd05-7a33-c931-b16e-a105f9a7c885",
            "path": [],
        },
        # 18
        {
            "id": "c0d9a49c-3fbf-4ef5-88fa-690d17b9ce02",
            "fromOperator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "fromConnector": "0e368818-fdfb-6796-a463-8bd9d5ff03e5",
            "toOperator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "toConnector": "54e9008c-0451-9e1c-c334-31e3887a4b07",
            "path": [],
        },
    ],
    "inputs": [
        # 0
        {
            "id": "8a569d4a-863a-4800-abb5-819cc1e8a030",
            "type": "INT",
            "name": "n_estimators",
            "posY": 240,
            "posX": 940,
            "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
            "connector": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 1
        {
            "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
            "type": "INT",
            "name": "n_grid",
            "posY": 90,
            "posX": -60,
            "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "connector": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 2
        {
            "id": "f468e81c-0e8f-4869-a268-892a391327d6",
            "type": "FLOAT",
            "name": "x_max",
            "posY": 120,
            "posX": -60,
            "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "connector": "02a7f8f6-0fb5-5a65-12d7-a21d61cdd271",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 3
        {
            "id": "d5c0c6b6-3b9d-48ed-9c40-70ecf14a3d0d",
            "type": "FLOAT",
            "name": "x_min",
            "posY": 150,
            "posX": -60,
            "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "connector": "4ef2610a-4321-004c-aee8-5cbf87ac1a49",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 4
        {
            "id": "196c78f4-6b9a-4476-9b37-ec80986a6a47",
            "type": "SERIES",
            "name": "x_vals",
            "posY": 520,
            "posX": -50,
            "operator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
            "connector": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 5
        {
            "id": "1cabf944-d63e-4d0d-a1e7-d6c0ffb193c5",
            "type": "FLOAT",
            "name": "y_max",
            "posY": 180,
            "posX": -60,
            "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "connector": "80fb9d9d-d926-8cb6-6a41-777ba806f6ea",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 6
        {
            "id": "2c212317-15a7-4599-b1f2-b6333a6c7a2b",
            "type": "FLOAT",
            "name": "y_min",
            "posY": 210,
            "posX": -60,
            "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
            "connector": "b3492592-b3e8-caaa-a4d4-4670d110d7f0",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 7
        {
            "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
            "type": "SERIES",
            "name": "y_vals",
            "posY": 370,
            "posX": -50,
            "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
            "connector": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
            "constant": False,
            "constantValue": {"value": ""},
        },
        # 8
        {
            "id": "a062167b-8fe0-4a48-bd94-552039a4f7af",
            "type": "STRING",
            "name": "",
            "posY": 0,
            "posX": -200,
            "operator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
            "connector": "fc417e48-f7d8-0bbf-60ac-af92a9150170",
            "constant": True,
            "constantValue": {"value": "y"},
        },
        # 9
        {
            "id": "088d81cf-caa3-4fd4-ab7a-e1538de3b559",
            "type": "STRING",
            "posY": 0,
            "posX": -200,
            "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
            "connector": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
            "constant": True,
            "constantValue": {"value": "y"},
        },
        # 10
        {
            "id": "d4ee291f-4476-447d-a161-a6b16fdaf205",
            "type": "STRING",
            "posY": 0,
            "posX": -200,
            "operator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
            "connector": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
            "constant": True,
            "constantValue": {"value": "x"},
        },
    ],
    "outputs": [
        {
            "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
            "type": "PLOTLYJSON",
            "name": "contour_plot",
            "posY": -100,
            "posX": 2010,
            "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
            "connector": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
            "constant": False,
            "constantValue": {"value": ""},
        }
    ],
    "wirings": [
        {
            "id": "2634db74-157b-4c07-a49d-6aedc6f9a7bc",
            "name": "STANDARD-WIRING",
            "inputWirings": [
                {
                    "id": "2ff1b365-0e29-4253-bfa0-a1474f2fb2cd",
                    "workflowInputName": "x_vals",
                    "adapterId": "direct_provisioning",
                    "filters": {
                        "value": [
                            1.1843789383694558,
                            1.4510047706096545,
                            1.2788758326875431,
                            0.37509562822595954,
                            -0.34833296100822775,
                            1.1273700107814664,
                            -0.5828114496740056,
                            -0.6019201001434932,
                            0.14597543451058187,
                            0.4926503544251617,
                            0.2154680856803482,
                            -0.2551963406058142,
                            -0.002139457430137104,
                            0.8030161690272482,
                            -0.3932162493293685,
                            0.04430883519637191,
                            0.7563416189031987,
                            0.2806832923291206,
                            -0.08208686777845176,
                            0.653910377510926,
                            0.6807191115282479,
                            0.634442822437029,
                            0.6345290120742698,
                            0.25383982484036116,
                            0.09012530518517568,
                            0.5408800137167201,
                            -0.364037407191779,
                            0.2546865562237355,
                            -0.715008247735518,
                            -0.2621021415447864,
                        ]
                    },
                },
                {
                    "id": "cf8a7ad8-cdf3-484e-83a1-23fd55a1cffd",
                    "workflowInputName": "y_vals",
                    "adapterId": "direct_provisioning",
                    "filters": {
                        "value": [
                            1.5986223975391751,
                            2.1774012998349765,
                            1.7434766038349168,
                            1.210123795100509,
                            1.753978223324373,
                            0.8933229057108552,
                            0.24746883487630933,
                            0.11100046749003192,
                            0.08733786278367306,
                            0.1788892936949697,
                            0.18430378100996064,
                            0.07471532585846613,
                            0.2769387623394832,
                            -0.09008184046979803,
                            0.07339491751946536,
                            0.28334568317103104,
                            0.008365597726208943,
                            0.3372043953342152,
                            0.22858171831554708,
                            0.008250420561521699,
                            0.3074906219622352,
                            0.11450092763470078,
                            0.20194233068818632,
                            0.0008354561561721291,
                            -0.11307439734807545,
                            -0.2473543352654944,
                            -0.0006302527890497539,
                            0.08514825206658988,
                            0.29330191199417466,
                            0.4601618524597455,
                        ]
                    },
                },
                {
                    "id": "5021c197-3c38-4e66-b4dc-20e6b5a75bdc",
                    "workflowInputName": "n_estimators",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": 100},
                },
                {
                    "id": "93292699-90f1-41ec-b11c-4538521a64f0",
                    "workflowInputName": "n_grid",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": 30},
                },
                {
                    "id": "1aedec9f-9c37-4894-b462-c787c9ec8593",
                    "workflowInputName": "x_max",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": 3},
                },
                {
                    "id": "327ddb6a-f21c-4c2c-a3a0-cfd3105c3015",
                    "workflowInputName": "x_min",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": -3},
                },
                {
                    "id": "0de8335d-b104-4ca4-b0fc-4066eb1f3ae6",
                    "workflowInputName": "y_max",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": 3},
                },
                {
                    "id": "552a8f95-9e8f-474b-b28c-652ae26ab1c2",
                    "workflowInputName": "y_min",
                    "adapterId": "direct_provisioning",
                    "filters": {"value": -3},
                },
            ],
            "outputWirings": [
                {
                    "id": "4c6034e9-1f58-4b98-b6a5-68231a41e08a",
                    "workflowOutputName": "contour_plot",
                    "adapterId": "direct_provisioning",
                },
                {
                    "id": "d01005c7-552c-48a4-972c-28cd7044597a",
                    "workflowOutputName": "xs",
                    "adapterId": "direct_provisioning",
                },
            ],
        }
    ],
}

valid_input_with_name: dict = valid_workflow_example_iso_forest["inputs"][0]
valid_input_without_name: dict = valid_workflow_example_iso_forest["inputs"][8]


def test_io_validator_name_valid_python_identifier_accepts_valid_io():
    WorkflowIoFrontendDto(**valid_input_with_name)


def test_io_validator_name_valid_python_identifier_identifies_keyword_name():
    input_with_keyword_name = deepcopy(valid_input_with_name)
    print(input_with_keyword_name.keys())
    input_with_keyword_name["name"] = "pass"
    print(input_with_keyword_name["name"])

    with pytest.raises(ValueError) as exc:
        WorkflowIoFrontendDto(**input_with_keyword_name)

    assert "not a valid Python identifier" in str(exc.value)


def test_io_validator_name_valid_python_identifier_identifies_invalid_name():
    input_with_invalid_name = deepcopy(valid_input_with_name)
    input_with_invalid_name["name"] = "1name"

    with pytest.raises(ValueError) as exc:
        WorkflowIoFrontendDto(**input_with_invalid_name)

    assert "not a valid Python identifier" in str(exc.value)


def test_io_validators_accept_valid_io_without_constant_value():
    WorkflowIoFrontendDto(**valid_input_with_name)


def test_io_validators_accept_valid_io_without_name():
    WorkflowIoFrontendDto(**valid_input_without_name)


valid_operator = valid_workflow_example_iso_forest["operators"][0]


def test_operator_validators_accept_valid_operator():
    WorkflowOperatorFrontendDto(**valid_operator)


def test_operator_validator_is_released_identifies_state_other_than_released():
    operator_with_invalid_state = deepcopy(valid_operator)
    operator_with_invalid_state["state"] = "DRAFT"

    with pytest.raises(ValueError) as exc:
        WorkflowOperatorFrontendDto(**operator_with_invalid_state)

    assert "released" in str(exc.value)


valid_link_json = valid_workflow_example_iso_forest["links"][0]


def test_link_validators_accept_valid_link():
    WorkflowLinkFrontendDto(**valid_link_json)


def test_link_validator_no_self_reference_identifies_self_reference():
    link_with_self_reference = deepcopy(valid_link_json)
    print(link_with_self_reference.keys())
    link_with_self_reference["toOperator"] = link_with_self_reference["fromOperator"]

    with pytest.raises(ValueError) as exc:
        WorkflowLinkFrontendDto(**link_with_self_reference)

    assert "must differ" in str(exc.value)


valid_wiring = valid_workflow_example_iso_forest["wirings"][0]
valid_input_wiring = valid_wiring["inputWirings"][0]


def test_wiring_validators_accept_valid_wiring():
    WiringFrontendDto(**valid_wiring)


def test_parent_validator_tag_not_latest_identifies_tag_latest():
    workflow_tagged_latest = deepcopy(valid_workflow_example_iso_forest)
    workflow_tagged_latest["tag"] = "latest"

    with pytest.raises(ValueError) as exc:
        WorkflowRevisionFrontendDto(**workflow_tagged_latest)

    assert "internal use only" in str(exc.value)


def test_workflow_validators_accept_valid_workflow():
    workflow_dto = WorkflowRevisionFrontendDto(**valid_workflow_example_iso_forest)

    assert len(workflow_dto.operators) == len(
        valid_workflow_example_iso_forest["operators"]
    )
    assert len(workflow_dto.links) == len(valid_workflow_example_iso_forest["links"])
    assert len(workflow_dto.inputs) == len(valid_workflow_example_iso_forest["inputs"])
    assert len(workflow_dto.outputs) == len(
        valid_workflow_example_iso_forest["outputs"]
    )


def test_workflow_validator_input_names_none_or_unique_identifies_double_name():
    workflow_with_double_input_name = deepcopy(valid_workflow_example_iso_forest)
    workflow_with_double_input_name["inputs"][1][
        "name"
    ] = workflow_with_double_input_name["inputs"][0]["name"]

    with pytest.raises(ValueError) as exc:
        WorkflowRevisionFrontendDto(**workflow_with_double_input_name)

    assert "duplicates" in str(exc.value)


def test_workflow_validator_determine_outputs_from_operators_and_links_removes_unlinked_output():
    workflow_with_unlinked_output = deepcopy(valid_workflow_example_iso_forest)
    workflow_with_unlinked_output["outputs"].append(
        workflow_with_unlinked_output["outputs"][0]
    )

    workflow_dto = WorkflowRevisionFrontendDto(**workflow_with_unlinked_output)

    assert len(workflow_dto.outputs) == len(
        valid_workflow_example_iso_forest["outputs"]
    )


def test_workflow_validator_name_or_constant_data_provided_identifies_io_without_name_and_constant_value():
    workflow_io_with_no_name_no_value = deepcopy(valid_workflow_example_iso_forest)
    del workflow_io_with_no_name_no_value["inputs"][0]["name"]

    with pytest.raises(ValueError) as exc:
        workflow_dto = WorkflowRevisionFrontendDto(**workflow_io_with_no_name_no_value)

    assert "Either name or constant data" in str(exc.value)


def test_workflow_validator_name_or_constant_data_provided_identifies_io_with_name_and_constant_true():
    workflow_with_input_with_name_and_constant_true = deepcopy(
        valid_workflow_example_iso_forest
    )
    workflow_with_input_with_name_and_constant_true["inputs"][0]["constant"] = True

    with pytest.raises(ValueError) as exc:
        WorkflowRevisionFrontendDto(**workflow_with_input_with_name_and_constant_true)

    assert "constant must be false" in str(exc.value)


def test_workflow_validator_links_acyclic_directed_graph_identifies_cyclic_links():
    workflow_with_cyclic_links = deepcopy(valid_workflow_example_iso_forest)
    # Change link #11 with id "54162076-43a3-4ac1-ab30-9854b5a1ac0b"
    # from operator "Isolation Forest"
    # with id "d1b7342b-0efa-4a01-b239-d82834d1583f" and
    # output connector "decision_function_values" with id "4594161b-f878-09c3-ab66-c1803728ea62"
    # into operator "Contour Plot" with id "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b" and
    # input connector "z"  with id "455f7a00-c731-b2ba-ee84-8d8b567bd50e"
    # to link into operator "Combine as named column into DataFrame"
    # with id "2ae1a251-3d86-4323-ae64-0702cfb5a4cf" and
    # input connector "series" with id "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab"
    workflow_with_cyclic_links["links"][11][
        "toOperator"
    ] = valid_workflow_example_iso_forest["links"][1]["toOperator"]
    workflow_with_cyclic_links["links"][11][
        "toConnector"
    ] = valid_workflow_example_iso_forest["links"][1]["toConnector"]

    # Change link #1 with id "e9fa0523-dfc8-4c47-ab9b-7ac64eff87ea"
    # from operator #0 "Name Series (2)" with id "1ecddb98-6ae1-48b0-b125-20d3b4e3118c" and
    # output connector "output" with id "44dc198e-d6b6-535f-f2c8-c8bae74acdf1"
    # into operator "Combine as named column into DataFrame"
    # with id "2ae1a251-3d86-4323-ae64-0702cfb5a4cf" and
    # input connector "series" with id "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab"
    # to link into operator "Contour Plot" with id "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b" and
    # input connector "z" with id "455f7a00-c731-b2ba-ee84-8d8b567bd50e"
    workflow_with_cyclic_links["links"][1][
        "toOperator"
    ] = valid_workflow_example_iso_forest["links"][11]["toOperator"]
    workflow_with_cyclic_links["links"][1][
        "toConnector"
    ] = valid_workflow_example_iso_forest["links"][11]["toConnector"]

    with pytest.raises(ValueError) as exc:
        WorkflowRevisionFrontendDto(**workflow_with_cyclic_links)

    assert "may not form any loop" in str(exc.value)


def test_to_link():
    from_connector = ConnectorFrontendDto(
        **{
            "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
            "type": "SERIES",
            "name": "output",
            "posY": 0,
            "posX": 0,
        }
    )
    to_connector = ConnectorFrontendDto(
        **{
            "id": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
            "type": "ANY",
            "name": "series_or_dataframe",
            "posY": 0,
            "posX": 0,
        },
    )
    link = WorkflowLinkFrontendDto(**valid_link_json).to_link(
        from_connector, to_connector, UUID(valid_workflow_example_iso_forest["id"])
    )

    assert str(link.id) == valid_link_json["id"]
    assert str(link.start.operator) == valid_link_json["fromOperator"]
    assert str(link.start.connector.id) == valid_link_json["fromConnector"]
    assert str(link.end.operator) == valid_link_json["toOperator"]
    assert str(link.end.connector.id) == valid_link_json["toConnector"]


def test_from_link():
    from_connector = ConnectorFrontendDto(
        **{
            "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
            "type": "SERIES",
            "name": "output",
            "posY": 0,
            "posX": 0,
        }
    )
    to_connector = ConnectorFrontendDto(
        **{
            "id": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
            "type": "ANY",
            "name": "series_or_dataframe",
            "posY": 0,
            "posX": 0,
        },
    )
    link = WorkflowLinkFrontendDto(**valid_link_json).to_link(
        from_connector, to_connector, UUID(valid_workflow_example_iso_forest["id"])
    )
    link_dto = WorkflowLinkFrontendDto.from_link(
        link, UUID(valid_workflow_example_iso_forest["id"])
    )

    assert str(link_dto.id) == valid_link_json["id"]
    assert str(link_dto.from_operator) == valid_link_json["fromOperator"]
    assert str(link_dto.from_connector) == valid_link_json["fromConnector"]
    assert str(link_dto.to_operator) == valid_link_json["toOperator"]
    assert str(link_dto.to_connector) == valid_link_json["toConnector"]


def test_io_to_io():
    io = WorkflowIoFrontendDto(**valid_input_with_name).to_io()

    assert str(io.id) == valid_input_with_name["id"]
    assert io.name == valid_input_with_name["name"]
    assert io.data_type == valid_input_with_name["type"]


def test_connector_to_connector():
    valid_connector = valid_operator["inputs"][0]
    connector = ConnectorFrontendDto(**valid_connector).to_connector()

    assert str(connector.id) == valid_connector["id"]
    assert connector.name == valid_connector["name"]
    assert connector.position.x == valid_connector["posX"]
    assert connector.position.y == valid_connector["posY"]
    assert connector.data_type == valid_connector["type"]


def test_connector_from_connector():
    valid_connector = valid_operator["inputs"][0]
    connector = ConnectorFrontendDto(**valid_connector).to_connector()
    connector_dto = ConnectorFrontendDto.from_connector(connector)

    assert str(connector_dto.id) == valid_connector["id"]
    assert connector_dto.name == valid_connector["name"]
    assert connector_dto.pos_x == valid_connector["posX"]
    assert connector_dto.pos_y == valid_connector["posY"]
    assert connector_dto.type == valid_connector["type"]


def test_to_operator():
    operator = WorkflowOperatorFrontendDto(**valid_operator).to_operator()

    assert str(operator.id) == valid_operator["id"]
    assert str(operator.revision_group_id) == valid_operator["groupId"]
    assert operator.name == valid_operator["name"]
    assert operator.type == valid_operator["type"]
    assert operator.state == valid_operator["state"]
    assert operator.version_tag == valid_operator["tag"]
    assert str(operator.transformation_id) == valid_operator["itemId"]
    assert len(operator.inputs) == len(valid_operator["inputs"])
    assert len(operator.outputs) == len(valid_operator["outputs"])
    assert operator.position.x == valid_operator["posX"]
    assert operator.position.y == valid_operator["posY"]


def test_from_operator():
    operator = WorkflowOperatorFrontendDto(**valid_operator).to_operator()
    operator_dto = WorkflowOperatorFrontendDto.from_operator(operator)

    assert str(operator_dto.id) == valid_operator["id"]
    assert str(operator_dto.group_id) == valid_operator["groupId"]
    assert operator_dto.name == valid_operator["name"]
    # assert operator_dto.description == valid_operator["description"]
    # assert operator_dto.category == valid_operator["category"]
    assert operator_dto.type == valid_operator["type"]
    assert operator_dto.state == valid_operator["state"]
    assert operator_dto.tag == valid_operator["tag"]
    assert str(operator_dto.transformation_id) == valid_operator["itemId"]
    assert len(operator_dto.inputs) == len(valid_operator["inputs"])
    assert len(operator_dto.outputs) == len(valid_operator["outputs"])
    assert operator_dto.pos_x == valid_operator["posX"]
    assert operator_dto.pos_y == valid_operator["posY"]


def test_io_to_io_connector():
    operators = [
        WorkflowOperatorFrontendDto(**operator).to_operator()
        for operator in valid_workflow_example_iso_forest["operators"]
    ]
    connector = WorkflowIoFrontendDto(**valid_input_with_name).to_io_connector(
        *get_operator_and_connector_name(
            valid_input_with_name["operator"],
            valid_input_with_name["connector"],
            operators,
        )
    )

    assert str(connector.id) == valid_input_with_name["id"]
    assert connector.name == valid_input_with_name["name"]
    assert connector.data_type == valid_input_with_name["type"]
    assert connector.position.x == valid_input_with_name["posX"]
    assert connector.position.y == valid_input_with_name["posY"]


def test_to_constant():
    operators = [
        WorkflowOperatorFrontendDto(**operator).to_operator()
        for operator in valid_workflow_example_iso_forest["operators"]
    ]

    constant = WorkflowIoFrontendDto(**valid_input_without_name).to_constant(
        *get_operator_and_connector_name(
            valid_input_with_name["operator"],
            valid_input_with_name["connector"],
            operators,
        )
    )

    assert str(constant.id) == valid_input_without_name["id"]
    assert constant.data_type == valid_input_without_name["type"]
    assert constant.position.x == valid_input_without_name["posX"]
    assert constant.position.y == valid_input_without_name["posY"]

    assert constant.value == valid_input_without_name["constantValue"]["value"]


def test_from_constant():
    operators = [
        WorkflowOperatorFrontendDto(**operator).to_operator()
        for operator in valid_workflow_example_iso_forest["operators"]
    ]

    constant = WorkflowIoFrontendDto(**valid_input_without_name).to_constant(
        *get_operator_and_connector_name(
            valid_input_with_name["operator"],
            valid_input_with_name["connector"],
            operators,
        )
    )
    io_dto: WorkflowIoFrontendDto = WorkflowIoFrontendDto.from_constant(
        constant,
        operator_id=UUID(valid_input_without_name["operator"]),
        connector_id=UUID(valid_input_without_name["connector"]),
    )

    assert str(io_dto.id) == valid_input_without_name["id"]
    assert io_dto.name is None
    assert io_dto.type == valid_input_without_name["type"]
    assert io_dto.pos_x == valid_input_without_name["posX"]
    assert io_dto.pos_y == valid_input_without_name["posY"]
    assert str(io_dto.operator) == valid_input_without_name["operator"]
    assert str(io_dto.connector) == valid_input_without_name["connector"]
    assert io_dto.constant == valid_input_without_name["constant"]
    assert io_dto.constant_value == valid_input_without_name["constantValue"]


def test_to_input_wiring():
    input_wiring = InputWiringFrontendDto(**valid_input_wiring).to_input_wiring()

    assert input_wiring.workflow_input_name == valid_input_wiring["workflowInputName"]
    assert input_wiring.adapter_id == valid_input_wiring["adapterId"]
    assert input_wiring.filters == valid_input_wiring["filters"]


def test_from_input_wiring():
    input_wiring = InputWiringFrontendDto(**valid_input_wiring).to_input_wiring()
    input_wiring_dto = InputWiringFrontendDto.from_input_wiring(input_wiring)

    assert (
        input_wiring_dto.workflow_input_name == valid_input_wiring["workflowInputName"]
    )
    assert input_wiring_dto.adapter_id == valid_input_wiring["adapterId"]
    assert input_wiring_dto.filters == valid_input_wiring["filters"]


def test_to_wiring():
    wiring = WiringFrontendDto(**valid_wiring).to_wiring()

    assert len(wiring.input_wirings) == len(valid_wiring["inputWirings"])
    assert len(wiring.output_wirings) == len(valid_wiring["outputWirings"])


def test_from_wiring():
    wiring = WiringFrontendDto(**valid_wiring).to_wiring()
    wiring_dto = WiringFrontendDto.from_wiring(
        wiring, valid_workflow_example_iso_forest["id"]
    )

    assert len(wiring_dto.input_wirings) == len(valid_wiring["inputWirings"])
    assert len(wiring_dto.output_wirings) == len(valid_wiring["outputWirings"])


def test_to_workflow_content():
    workflow_content = WorkflowRevisionFrontendDto(
        **valid_workflow_example_iso_forest
    ).to_workflow_content()

    assert len(workflow_content.links) - len(workflow_content.constants) == len(
        valid_workflow_example_iso_forest["links"]
    )
    assert len(workflow_content.inputs) + len(workflow_content.constants) == len(
        valid_workflow_example_iso_forest["inputs"]
    )
    assert len(workflow_content.outputs) == len(
        valid_workflow_example_iso_forest["outputs"]
    )
    assert len(workflow_content.operators) == len(
        valid_workflow_example_iso_forest["operators"]
    )


def test_io_from_io():
    input = WorkflowIoFrontendDto(**valid_input_with_name).to_io()
    workflow_content = WorkflowRevisionFrontendDto(
        **valid_workflow_example_iso_forest
    ).to_workflow_content()
    io_dto: WorkflowIoFrontendDto = WorkflowIoFrontendDto.from_io(
        input,
        valid_input_with_name["operator"],
        valid_input_with_name["connector"],
        *position_from_input_connector_id(input.id, workflow_content.inputs),
    )

    assert str(io_dto.id) == valid_input_with_name["id"]
    assert io_dto.name == valid_input_with_name["name"]
    assert io_dto.type == valid_input_with_name["type"]
    assert io_dto.pos_x == valid_input_with_name["posX"]
    assert io_dto.pos_y == valid_input_with_name["posY"]
    assert str(io_dto.operator) == valid_input_with_name["operator"]
    assert str(io_dto.connector) == valid_input_with_name["connector"]
    assert io_dto.constant == valid_input_with_name["constant"]


def test_workflow_dto_to_transformation_revision():
    transformation_revision = WorkflowRevisionFrontendDto(
        **valid_workflow_example_iso_forest
    ).to_transformation_revision()

    assert str(transformation_revision.id) == valid_workflow_example_iso_forest["id"]
    assert (
        str(transformation_revision.revision_group_id)
        == valid_workflow_example_iso_forest["groupId"]
    )
    assert transformation_revision.name == valid_workflow_example_iso_forest["name"]
    assert (
        transformation_revision.description
        == valid_workflow_example_iso_forest["description"]
    )
    assert (
        transformation_revision.category
        == valid_workflow_example_iso_forest["category"]
    )
    assert (
        transformation_revision.version_tag == valid_workflow_example_iso_forest["tag"]
    )
    assert transformation_revision.released_timestamp is not None
    assert transformation_revision.disabled_timestamp is None
    assert transformation_revision.state == valid_workflow_example_iso_forest["state"]
    assert transformation_revision.type == valid_workflow_example_iso_forest["type"]
    assert transformation_revision.documentation == ""
    assert (
        len(transformation_revision.io_interface.inputs)
        == len(valid_workflow_example_iso_forest["inputs"])
        - 3  # only non-constant inputs in TR
    )
    assert len(transformation_revision.io_interface.outputs) == len(
        valid_workflow_example_iso_forest["outputs"]
    )
    assert len(transformation_revision.test_wiring.input_wirings) == len(
        valid_workflow_example_iso_forest["wirings"][0]["inputWirings"]
    )
    assert len(transformation_revision.test_wiring.output_wirings) == len(
        valid_workflow_example_iso_forest["wirings"][0]["outputWirings"]
    )


def test_workflow_dto_from_transformation_revision():
    transformation_revision = WorkflowRevisionFrontendDto(
        **valid_workflow_example_iso_forest
    ).to_transformation_revision()
    workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )

    assert str(workflow_dto.id) == valid_workflow_example_iso_forest["id"]
    assert str(workflow_dto.group_id) == valid_workflow_example_iso_forest["groupId"]
    assert workflow_dto.name == valid_workflow_example_iso_forest["name"]
    assert workflow_dto.description == valid_workflow_example_iso_forest["description"]
    assert workflow_dto.category == valid_workflow_example_iso_forest["category"]
    assert workflow_dto.tag == valid_workflow_example_iso_forest["tag"]
    assert workflow_dto.state == valid_workflow_example_iso_forest["state"]
    assert workflow_dto.type == valid_workflow_example_iso_forest["type"]
    assert len(workflow_dto.inputs) == len(valid_workflow_example_iso_forest["inputs"])
    assert len(workflow_dto.outputs) == len(
        valid_workflow_example_iso_forest["outputs"]
    )
    assert len(workflow_dto.wirings[0].input_wirings) == len(
        valid_workflow_example_iso_forest["wirings"][0]["inputWirings"]
    )
    assert len(workflow_dto.wirings[0].output_wirings) == len(
        valid_workflow_example_iso_forest["wirings"][0]["outputWirings"]
    )


def test_workflow_dto_to_transformation_revision_and_back_matches():
    workflow_dto = WorkflowRevisionFrontendDto(**valid_workflow_example_iso_forest)
    transformation_revision = workflow_dto.to_transformation_revision()
    returned_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )

    assert len(workflow_dto.links) == len(returned_workflow_dto.links)
    for i in range(len(workflow_dto.links)):
        assert workflow_dto.links[i] == returned_workflow_dto.links[i]
    assert len(workflow_dto.inputs) == len(returned_workflow_dto.inputs)
    for i in range(len(workflow_dto.inputs)):
        assert workflow_dto.inputs[i].id == returned_workflow_dto.inputs[i].id
        assert workflow_dto.inputs[i].type == returned_workflow_dto.inputs[i].type
        assert (
            workflow_dto.inputs[i].operator == returned_workflow_dto.inputs[i].operator
        )
        assert (
            workflow_dto.inputs[i].connector
            == returned_workflow_dto.inputs[i].connector
        )
        assert workflow_dto.inputs[i].pos_x == returned_workflow_dto.inputs[i].pos_x
        assert workflow_dto.inputs[i].pos_y == returned_workflow_dto.inputs[i].pos_y
        assert (
            workflow_dto.inputs[i].constant == returned_workflow_dto.inputs[i].constant
        )
        assert (
            workflow_dto.inputs[i].constant_value
            == returned_workflow_dto.inputs[i].constant_value
        )
        if not workflow_dto.inputs[i].constant:
            assert workflow_dto.inputs[i].name == returned_workflow_dto.inputs[i].name
    assert len(workflow_dto.outputs) == len(returned_workflow_dto.outputs)
    for i in range(len(workflow_dto.outputs)):
        assert workflow_dto.outputs[i] == returned_workflow_dto.outputs[i]
    assert len(workflow_dto.operators) == len(returned_workflow_dto.operators)
    for i in range(len(workflow_dto.operators)):
        assert workflow_dto.operators[i].id == returned_workflow_dto.operators[i].id
        assert (
            workflow_dto.operators[i].group_id
            == returned_workflow_dto.operators[i].group_id
        )
        assert (
            workflow_dto.operators[i].transformation_id
            == returned_workflow_dto.operators[i].transformation_id
        )
        assert workflow_dto.operators[i].tag == returned_workflow_dto.operators[i].tag
        assert workflow_dto.operators[i].name == returned_workflow_dto.operators[i].name
        assert (
            workflow_dto.operators[i].inputs
            == returned_workflow_dto.operators[i].inputs
        )
        assert (
            workflow_dto.operators[i].outputs
            == returned_workflow_dto.operators[i].outputs
        )
        assert (
            workflow_dto.operators[i].pos_x == returned_workflow_dto.operators[i].pos_x
        )
        assert (
            workflow_dto.operators[i].pos_y == returned_workflow_dto.operators[i].pos_y
        )


def test_workflow_dto_from_transformation_revision_and_back_matches():
    workflow_dto = WorkflowRevisionFrontendDto(**valid_workflow_example_iso_forest)
    transformation_revision = workflow_dto.to_transformation_revision()
    returned_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )
    returned_transformation_revision = returned_workflow_dto.to_transformation_revision(
        timestamp=transformation_revision.released_timestamp
    )

    assert (
        transformation_revision.released_timestamp
        == returned_transformation_revision.released_timestamp
    )
    assert len(transformation_revision.io_interface.inputs) == len(
        returned_transformation_revision.io_interface.inputs
    )
    for i in range(len(transformation_revision.io_interface.inputs)):
        assert (
            transformation_revision.io_interface.inputs[i]
            == returned_transformation_revision.io_interface.inputs[i]
        )
    assert len(transformation_revision.io_interface.outputs) == len(
        returned_transformation_revision.io_interface.outputs
    )
    for i in range(len(transformation_revision.io_interface.outputs)):
        assert (
            transformation_revision.io_interface.outputs[i]
            == returned_transformation_revision.io_interface.outputs[i]
        )
    assert len(transformation_revision.content.links) == len(
        returned_transformation_revision.content.links
    )
    for i in range(len(transformation_revision.content.links)):
        assert (
            transformation_revision.content.links[i]
            == returned_transformation_revision.content.links[i]
        )
    assert len(transformation_revision.content.inputs) == len(
        returned_transformation_revision.content.inputs
    )
    for i in range(len(transformation_revision.content.inputs)):
        assert (
            transformation_revision.content.inputs[i]
            == returned_transformation_revision.content.inputs[i]
        )
    assert len(transformation_revision.content.constants) == len(
        returned_transformation_revision.content.constants
    )
    for i in range(len(transformation_revision.content.constants)):
        assert (
            transformation_revision.content.constants[i]
            == returned_transformation_revision.content.constants[i]
        )
    assert len(transformation_revision.content.outputs) == len(
        returned_transformation_revision.content.outputs
    )
    for i in range(len(transformation_revision.content.outputs)):
        assert (
            transformation_revision.content.outputs[i]
            == returned_transformation_revision.content.outputs[i]
        )
    assert len(transformation_revision.content.operators) == len(
        returned_transformation_revision.content.operators
    )
    for i in range(len(transformation_revision.content.operators)):
        assert (
            transformation_revision.content.operators[i]
            == returned_transformation_revision.content.operators[i]
        )
    assert transformation_revision == returned_transformation_revision


def test_workflow_dto_to_transformation_revision_and_back_matches_with_ambiguous_open_ends():
    open_ends_workflow = deepcopy(valid_workflow_example_iso_forest)
    open_ends_workflow["state"] = "DRAFT"
    del open_ends_workflow["links"][16]
    del open_ends_workflow["links"][5]
    del open_ends_workflow["links"][1]
    del open_ends_workflow["links"][0]
    del open_ends_workflow["inputs"][7]
    del open_ends_workflow["inputs"][4]
    workflow_dto = WorkflowRevisionFrontendDto(**open_ends_workflow)
    transformation_revision = workflow_dto.to_transformation_revision()
    returned_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )

    assert len(workflow_dto.links) == len(returned_workflow_dto.links)
    for i in range(len(workflow_dto.links)):
        assert workflow_dto.links[i] == returned_workflow_dto.links[i]
    assert len(workflow_dto.inputs) == len(returned_workflow_dto.inputs)
    for i in range(len(workflow_dto.inputs)):
        assert workflow_dto.inputs[i].type == returned_workflow_dto.inputs[i].type
        assert (
            workflow_dto.inputs[i].operator == returned_workflow_dto.inputs[i].operator
        )
        assert (
            workflow_dto.inputs[i].connector
            == returned_workflow_dto.inputs[i].connector
        )
        assert workflow_dto.inputs[i].pos_x == returned_workflow_dto.inputs[i].pos_x
        assert workflow_dto.inputs[i].pos_y == returned_workflow_dto.inputs[i].pos_y
        assert (
            workflow_dto.inputs[i].constant == returned_workflow_dto.inputs[i].constant
        )
        assert (
            workflow_dto.inputs[i].constant_value
            == returned_workflow_dto.inputs[i].constant_value
        )
        if not workflow_dto.inputs[i].constant:
            assert workflow_dto.inputs[i].name == returned_workflow_dto.inputs[i].name
    assert len(workflow_dto.outputs) == len(returned_workflow_dto.outputs)
    for i in range(len(workflow_dto.outputs)):
        assert workflow_dto.outputs[i].type == returned_workflow_dto.outputs[i].type
        assert (
            workflow_dto.outputs[i].operator
            == returned_workflow_dto.outputs[i].operator
        )
        assert (
            workflow_dto.outputs[i].connector
            == returned_workflow_dto.outputs[i].connector
        )
        assert workflow_dto.outputs[i].pos_x == returned_workflow_dto.outputs[i].pos_x
        assert workflow_dto.outputs[i].pos_y == returned_workflow_dto.outputs[i].pos_y
        assert (
            workflow_dto.outputs[i].constant
            == returned_workflow_dto.outputs[i].constant
        )
        assert (
            workflow_dto.outputs[i].constant_value
            == returned_workflow_dto.outputs[i].constant_value
        )
        if not workflow_dto.outputs[i].constant:
            assert workflow_dto.outputs[i].name == returned_workflow_dto.outputs[i].name
    assert len(workflow_dto.operators) == len(returned_workflow_dto.operators)
    for i in range(len(workflow_dto.operators)):
        assert workflow_dto.operators[i].id == returned_workflow_dto.operators[i].id
        assert (
            workflow_dto.operators[i].group_id
            == returned_workflow_dto.operators[i].group_id
        )
        assert (
            workflow_dto.operators[i].transformation_id
            == returned_workflow_dto.operators[i].transformation_id
        )
        assert workflow_dto.operators[i].tag == returned_workflow_dto.operators[i].tag
        assert workflow_dto.operators[i].name == returned_workflow_dto.operators[i].name
        assert (
            workflow_dto.operators[i].inputs
            == returned_workflow_dto.operators[i].inputs
        )
        assert (
            workflow_dto.operators[i].outputs
            == returned_workflow_dto.operators[i].outputs
        )
        assert (
            workflow_dto.operators[i].pos_x == returned_workflow_dto.operators[i].pos_x
        )
        assert (
            workflow_dto.operators[i].pos_y == returned_workflow_dto.operators[i].pos_y
        )


def test_workflow_dto_from_transformation_revision_and_back_matches_with_ambiguous_open_ends():
    open_ends_workflow = deepcopy(valid_workflow_example_iso_forest)
    open_ends_workflow["state"] = "DRAFT"
    del open_ends_workflow["links"][16]
    del open_ends_workflow["links"][5]
    del open_ends_workflow["links"][1]
    del open_ends_workflow["links"][0]
    del open_ends_workflow["inputs"][7]
    del open_ends_workflow["inputs"][4]
    workflow_dto = WorkflowRevisionFrontendDto(**open_ends_workflow)
    transformation_revision = workflow_dto.to_transformation_revision()
    returned_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )
    returned_transformation_revision = returned_workflow_dto.to_transformation_revision(
        timestamp=transformation_revision.released_timestamp
    )

    assert (
        transformation_revision.released_timestamp
        == returned_transformation_revision.released_timestamp
    )
    assert len(transformation_revision.io_interface.inputs) == len(
        returned_transformation_revision.io_interface.inputs
    )
    assert len(transformation_revision.io_interface.outputs) == len(
        returned_transformation_revision.io_interface.outputs
    )
    # inputs and outputs will be generated with arbitrary UUID by validators
    # for the open ends. Their ids won't be reproduced, no need to compare
    assert len(transformation_revision.content.links) == len(
        returned_transformation_revision.content.links
    )
    for i in range(len(transformation_revision.content.links)):
        assert (
            transformation_revision.content.links[i]
            == returned_transformation_revision.content.links[i]
        )
    assert len(transformation_revision.content.inputs) == len(
        returned_transformation_revision.content.inputs
    )
    for i in range(len(transformation_revision.content.inputs)):
        assert (
            transformation_revision.content.inputs[i].name
            == returned_transformation_revision.content.inputs[i].name
        )
        assert (
            transformation_revision.content.inputs[i].data_type
            == returned_transformation_revision.content.inputs[i].data_type
        )
        assert (
            transformation_revision.content.inputs[i].operator_id
            == returned_transformation_revision.content.inputs[i].operator_id
        )
        assert (
            transformation_revision.content.inputs[i].connector_id
            == returned_transformation_revision.content.inputs[i].connector_id
        )
        assert (
            transformation_revision.content.inputs[i].operator_name
            == returned_transformation_revision.content.inputs[i].operator_name
        )
        assert (
            transformation_revision.content.inputs[i].connector_name
            == returned_transformation_revision.content.inputs[i].connector_name
        )
        assert (
            transformation_revision.content.inputs[i].position
            == returned_transformation_revision.content.inputs[i].position
        )
    assert len(transformation_revision.content.constants) == len(
        returned_transformation_revision.content.constants
    )
    for i in range(len(transformation_revision.content.constants)):
        assert (
            transformation_revision.content.constants[i]
            == returned_transformation_revision.content.constants[i]
        )
    assert len(transformation_revision.content.outputs) == len(
        returned_transformation_revision.content.outputs
    )
    for i in range(len(transformation_revision.content.outputs)):
        assert (
            transformation_revision.content.outputs[i].name
            == returned_transformation_revision.content.outputs[i].name
        )
        assert (
            transformation_revision.content.outputs[i].data_type
            == returned_transformation_revision.content.outputs[i].data_type
        )
        assert (
            transformation_revision.content.outputs[i].operator_id
            == returned_transformation_revision.content.outputs[i].operator_id
        )
        assert (
            transformation_revision.content.outputs[i].connector_id
            == returned_transformation_revision.content.outputs[i].connector_id
        )
        assert (
            transformation_revision.content.outputs[i].operator_name
            == returned_transformation_revision.content.outputs[i].operator_name
        )
        assert (
            transformation_revision.content.outputs[i].connector_name
            == returned_transformation_revision.content.outputs[i].connector_name
        )
        assert (
            transformation_revision.content.outputs[i].position
            == returned_transformation_revision.content.outputs[i].position
        )
    assert len(transformation_revision.content.operators) == len(
        returned_transformation_revision.content.operators
    )
    for op, op_returned in zip(
        transformation_revision.content.operators,
        returned_transformation_revision.content.operators,
    ):
        assert op == op_returned
