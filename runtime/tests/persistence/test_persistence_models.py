from copy import deepcopy
from collections import namedtuple
from uuid import uuid4

import pytest

from pydantic import ValidationError

from hetdesrun.utils import State, Type, get_uuid_from_seed

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.execution import nested_nodes

from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.persistence.models.transformation import TransformationRevision

from hetdesrun.models.wiring import WorkflowWiring


tr_json_valid_released_example = {
    "id": "67c14cf2-cd4e-410e-9aca-6664273ccc3f",
    "revision_group_id": "b123bfb6-f8ee-422f-bbf8-01668a471e88",
    "name": "Iso Forest Example",
    "description": "Example of a simple Isolation Forest application",
    "category": "Examples",
    "version_tag": "1.0.0",
    "released_timestamp": "2021-12-06 10:37",
    "type": "WORKFLOW",
    "state": "RELEASED",
    "io_interface": {
        "inputs": [
            # 0
            {
                "id": "8a569d4a-863a-4800-abb5-819cc1e8a030",
                "data_type": "INT",
                "name": "n_estimators",
            },
            # 1
            {
                "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
                "data_type": "INT",
                "name": "n_grid",
            },
            # 2
            {
                "id": "f468e81c-0e8f-4869-a268-892a391327d6",
                "data_type": "FLOAT",
                "name": "x_max",
            },
            # 3
            {
                "id": "d5c0c6b6-3b9d-48ed-9c40-70ecf14a3d0d",
                "data_type": "FLOAT",
                "name": "x_min",
            },
            # 4
            {
                "id": "196c78f4-6b9a-4476-9b37-ec80986a6a47",
                "data_type": "SERIES",
                "name": "x_vals",
            },
            # 5
            {
                "id": "1cabf944-d63e-4d0d-a1e7-d6c0ffb193c5",
                "data_type": "FLOAT",
                "name": "y_max",
            },
            # 6
            {
                "id": "2c212317-15a7-4599-b1f2-b6333a6c7a2b",
                "data_type": "FLOAT",
                "name": "y_min",
            },
            # 7
            {
                "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
                "data_type": "SERIES",
                "name": "y_vals",
            },
        ],
        "outputs": [
            {
                "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
                "data_type": "PLOTLYJSON",
                "name": "contour_plot",
            }
        ],
    },
    "content": {
        "operators": [
            # 0
            {
                "id": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
                "name": "Name Series (2)",
                "description": "Give a name to a series",
                "category": "Connectors",
                "type": "COMPONENT",
                "state": "RELEASED",
                "version_tag": "1.0.0",
                "transformation_id": "a4064897-66d3-9601-328e-5ae9036665c5",
                "inputs": [
                    {
                        "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                        "data_type": "SERIES",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                        "data_type": "SERIES",
                        "name": "output",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "position": {"y": 310, "x": 170},
            },
            # 1
            {
                "id": "74608f8a-d973-4add-9764-ad3348b3bb57",
                "name": "2D Grid Generator",
                "description": "Generates 2 dimensional grids",
                "category": "Visualization",
                "type": "COMPONENT",
                "state": "RELEASED",
                "version_tag": "1.0.0",
                "transformation_id": "096c6181-4ba5-0ee7-361a-3c32eee8c0c2",
                "inputs": [
                    {
                        "id": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
                        "data_type": "INT",
                        "name": "n",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "02a7f8f6-0fb5-5a65-12d7-a21d61cdd271",
                        "data_type": "FLOAT",
                        "name": "x_max",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "4ef2610a-4321-004c-aee8-5cbf87ac1a49",
                        "data_type": "FLOAT",
                        "name": "x_min",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "80fb9d9d-d926-8cb6-6a41-777ba806f6ea",
                        "data_type": "FLOAT",
                        "name": "y_max",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "b3492592-b3e8-caaa-a4d4-4670d110d7f0",
                        "data_type": "FLOAT",
                        "name": "y_min",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "474c27a3-df58-7b9f-ff7e-d57a2e416fb9",
                        "data_type": "SERIES",
                        "name": "x_indices",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "597905f3-db79-f46b-db04-dc22cdadf449",
                        "data_type": "SERIES",
                        "name": "x_values",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "0e368818-fdfb-6796-a463-8bd9d5ff03e5",
                        "data_type": "SERIES",
                        "name": "y_indices",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "38be3a38-8761-fc80-cab0-da2c12f4a9c8",
                        "data_type": "SERIES",
                        "name": "y_values",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "position": {"y": 30, "x": 160},
            },
            # 2
            {
                "id": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                "name": "Isolation Forest",
                "description": "A Isolation Forest Model",
                "category": "Anomaly Detection",
                "type": "COMPONENT",
                "state": "RELEASED",
                "version_tag": "1.0.0",
                "transformation_id": "cdec1d55-5bb6-8e8d-4571-fbc0ebf5a354",
                "inputs": [
                    {
                        "id": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
                        "data_type": "INT",
                        "name": "n_estimators",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "bc5ae666-e1fb-9189-8f72-d681eb5dcfde",
                        "data_type": "DATAFRAME",
                        "name": "test_data",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "017e5542-46dd-e1aa-d6f8-4026dcad3d44",
                        "data_type": "DATAFRAME",
                        "name": "train_data",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "4594161b-f878-09c3-ab66-c1803728ea62",
                        "data_type": "SERIES",
                        "name": "decision_function_values",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "68234ebe-51c0-96b9-c95b-86548f09e79c",
                        "data_type": "ANY",
                        "name": "trained_model",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "position": {"y": 180, "x": 1190},
            },
            # 3
            {
                "id": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
                "name": "Combine as named column into DataFrame",
                "description": "Combine as named column into a DataFrame.",
                "category": "Connectors",
                "type": "COMPONENT",
                "state": "RELEASED",
                "version_tag": "1.0.0",
                "transformation_id": "0d08af64-3f34-cddc-354b-d6a26c3f1aab",
                "inputs": [
                    {
                        "id": "fc417e48-f7d8-0bbf-60ac-af92a9150170",
                        "data_type": "STRING",
                        "name": "column_name",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab",
                        "data_type": "SERIES",
                        "name": "series",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
                        "data_type": "ANY",
                        "name": "series_or_dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "2bad1916-9d38-2409-b236-ebfce1fc1fae",
                        "data_type": "DATAFRAME",
                        "name": "dataframe",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "position": {"y": 280, "x": 705},
            },
            # 4
            {
                "id": "177db51b-6a68-4808-8e09-1a6d87f3e579",
                "groupId": "a4064897-66d3-9601-328e-5ae9036665c5",
                "name": "Name Series",
                "description": "Give a name to a series",
                "category": "Connectors",
                "type": "COMPONENT",
                "state": "RELEASED",
                "version_tag": "1.0.0",
                "transformation_id": "a4064897-66d3-9601-328e-5ae9036665c5",
                "inputs": [
                    {
                        "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                        "data_type": "SERIES",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                        "data_type": "SERIES",
                        "name": "output",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "position": {"y": 460, "x": 175},
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
                "version_tag": "1.0.0",
                "transformation_id": "68f91351-a1f5-9959-414a-2c72003f3226",
                "inputs": [
                    {
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "data_type": "SERIES",
                        "name": "series",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "data_type": "ANY",
                        "name": "series_or_dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "data_type": "DATAFRAME",
                        "name": "dataframe",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "position": {"y": 120, "x": 700},
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
                "version_tag": "1.0.0",
                "transformation_id": "d1fb4ae5-ef27-26b8-7a58-40b7cd8412e7",
                "inputs": [
                    {
                        "id": "b7803aec-db20-6bea-970f-0566ded49a7c",
                        "data_type": "ANY",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "outputs": [],
                "position": {"y": 210, "x": 1610},
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
                "version_tag": "1.0.0",
                "transformation_id": "f7530499-51b2-dd01-0d21-c24ee6f8c37e",
                "inputs": [
                    {
                        "id": "829cbd05-7a33-c931-b16e-a105f9a7c885",
                        "data_type": "SERIES",
                        "name": "x",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "54e9008c-0451-9e1c-c334-31e3887a4b07",
                        "data_type": "SERIES",
                        "name": "y",
                        "position": {"y": 0, "x": 0},
                    },
                    {
                        "id": "455f7a00-c731-b2ba-ee84-8d8b567bd50e",
                        "data_type": "SERIES",
                        "name": "z",
                        "position": {"y": 0, "x": 0},
                    },
                ],
                "outputs": [
                    {
                        "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
                        "data_type": "PLOTLYJSON",
                        "name": "contour_plot",
                        "position": {"y": 0, "x": 0},
                    }
                ],
                "position": {"y": -160, "x": 1610},
            },
        ],
        "links": [
            # 0
            {
                "id": "4497b894-dba0-4555-8b63-eb2b993c7592",
                "start": {
                    "operator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
                    "connector": {
                        "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                        "data_type": "SERIES",
                        "name": "output",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
                    "connector": {
                        "id": "801659c5-4c57-0dc6-df28-6d4f5412f44f",
                        "data_type": "ANY",
                        "name": "series_or_dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 1
            {
                "id": "e9fa0523-dfc8-4c47-ab9b-7ac64eff87ea",
                "start": {
                    "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
                    "connector": {
                        "id": "44dc198e-d6b6-535f-f2c8-c8bae74acdf1",
                        "data_type": "SERIES",
                        "name": "output",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
                    "connector": {
                        "id": "3e1b0bf1-48d3-a534-5a6f-fa1bb37a7aab",
                        "data_type": "SERIES",
                        "name": "series",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 2
            {
                "id": "8bf65f5f-7267-4ace-b137-2ba57500c4df",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "196c78f4-6b9a-4476-9b37-ec80986a6a47",
                        "data_type": "SERIES",
                        "name": "x_vals",
                        "position": {"y": 520, "x": -50},
                    },
                },
                "end": {
                    "operator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
                    "connector": {
                        "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                        "data_type": "SERIES",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 3
            {
                "id": "2f1644a8-6638-4c54-a343-6300f001d693",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
                        "data_type": "SERIES",
                        "name": "y_vals",
                        "position": {"y": 370, "x": -50},
                    },
                },
                "end": {
                    "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
                    "connector": {
                        "id": "5336c0a5-97ac-d436-ae5f-ee75fa8c8b40",
                        "data_type": "SERIES",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 4
            {
                "id": "0f52855d-a57b-4ac5-a5f8-db3eadb51240",
                "start": {
                    "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
                    "connector": {
                        "id": "53dff70b-364f-e5b7-fbb4-c293a5d2f339",
                        "data_type": "PLOTLYJSON",
                        "name": "contour_plot",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": None,
                    "connector": {
                        "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
                        "data_type": "PLOTLYJSON",
                        "name": "contour_plot",
                        "position": {"y": -100, "x": 2010},
                    },
                },
                "path": [],
            },
            # 5
            {
                "id": "4281ddc6-af44-4e72-bbdc-f2a7e9cef9fc",
                "start": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "597905f3-db79-f46b-db04-dc22cdadf449",
                        "data_type": "SERIES",
                        "name": "x_values",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
                    "connector": {
                        "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
                        "data_type": "ANY",
                        "name": "series_or_dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 6
            {
                "id": "0f2c8fd5-2032-4f0a-9bb7-39054ae7e4c5",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
                        "data_type": "INT",
                        "name": "n_grid",
                        "position": {"y": 90, "x": -60},
                    },
                },
                "end": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "64245bba-7e81-ef0a-941d-2f9b5b43d044",
                        "data_type": "INT",
                        "name": "n",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 7
            {
                "id": "deb0c00b-88c7-4930-8c22-12d18c395fdd",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "f468e81c-0e8f-4869-a268-892a391327d6",
                        "data_type": "FLOAT",
                        "name": "x_max",
                        "position": {"y": 120, "x": -60},
                    },
                },
                "end": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "02a7f8f6-0fb5-5a65-12d7-a21d61cdd271",
                        "data_type": "FLOAT",
                        "name": "x_max",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 8
            {
                "id": "978a06f2-1e4c-4df2-bbb6-e3e7bbd43929",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "d5c0c6b6-3b9d-48ed-9c40-70ecf14a3d0d",
                        "data_type": "FLOAT",
                        "name": "x_min",
                        "position": {"y": 150, "x": -60},
                    },
                },
                "end": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "4ef2610a-4321-004c-aee8-5cbf87ac1a49",
                        "data_type": "FLOAT",
                        "name": "x_min",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 9
            {
                "id": "89c5c8fb-dad1-402e-9ad9-787ab19b762b",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "1cabf944-d63e-4d0d-a1e7-d6c0ffb193c5",
                        "data_type": "FLOAT",
                        "name": "y_max",
                        "position": {"y": 180, "x": -60},
                    },
                },
                "end": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "80fb9d9d-d926-8cb6-6a41-777ba806f6ea",
                        "data_type": "FLOAT",
                        "name": "y_max",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 10
            {
                "id": "81604791-271e-4c79-9f08-19cbf260d39f",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "2c212317-15a7-4599-b1f2-b6333a6c7a2b",
                        "data_type": "FLOAT",
                        "name": "y_min",
                        "position": {"y": 210, "x": -60},
                    },
                },
                "end": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "b3492592-b3e8-caaa-a4d4-4670d110d7f0",
                        "data_type": "FLOAT",
                        "name": "y_min",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 11
            {
                "id": "54162076-43a3-4ac1-ab30-9854b5a1ac0b",
                "start": {
                    "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                    "connector": {
                        "id": "4594161b-f878-09c3-ab66-c1803728ea62",
                        "data_type": "SERIES",
                        "name": "decision_function_values",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
                    "connector": {
                        "id": "455f7a00-c731-b2ba-ee84-8d8b567bd50e",
                        "data_type": "SERIES",
                        "name": "z",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 12
            {
                "id": "fb64fdd5-d9b2-4e73-a480-3436d150d49f",
                "start": {
                    "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                    "connector": {
                        "id": "68234ebe-51c0-96b9-c95b-86548f09e79c",
                        "data_type": "ANY",
                        "name": "trained_model",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "4983a39a-88c8-4683-a79d-9321eabe30eb",
                    "connector": {
                        "id": "b7803aec-db20-6bea-970f-0566ded49a7c",
                        "data_type": "ANY",
                        "name": "input",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 13
            {
                "id": "dc00bb92-a52e-4a8a-a91c-6c88cd85f9f1",
                "start": {
                    "operator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
                    "connector": {
                        "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
                        "data_type": "DATAFRAME",
                        "name": "dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                    "connector": {
                        "id": "bc5ae666-e1fb-9189-8f72-d681eb5dcfde",
                        "data_type": "DATAFRAME",
                        "name": "test_data",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 14
            {
                "id": "23fc5984-daf8-482b-859b-3a8eef53f0ce",
                "start": {
                    "operator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
                    "connector": {
                        "id": "2bad1916-9d38-2409-b236-ebfce1fc1fae",
                        "data_type": "DATAFRAME",
                        "name": "dataframe",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                    "connector": {
                        "id": "017e5542-46dd-e1aa-d6f8-4026dcad3d44",
                        "data_type": "DATAFRAME",
                        "name": "train_data",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 15
            {
                "id": "a8afb568-965a-4ea0-aaa6-bb23dd373ed5",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "8a569d4a-863a-4800-abb5-819cc1e8a030",
                        "data_type": "INT",
                        "name": "n_estimators",
                        "position": {"y": 240, "x": 940},
                    },
                },
                "end": {
                    "operator": "d1b7342b-0efa-4a01-b239-d82834d1583f",
                    "connector": {
                        "id": "9861c5a4-1e37-54af-70be-f4e7b81d1f64",
                        "data_type": "INT",
                        "name": "n_estimators",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 16
            {
                "id": "4001126b-12d1-4879-b911-f5dcd60c9aca",
                "start": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "38be3a38-8761-fc80-cab0-da2c12f4a9c8",
                        "data_type": "SERIES",
                        "name": "y_values",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "3fdbf041-322b-4c7b-b953-10f6cef4b905",
                    "connector": {
                        "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
                        "data_type": "SERIES",
                        "name": "series",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 17
            {
                "id": "8ca7a384-d0eb-4871-8022-6097bd5dce0c",
                "start": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "474c27a3-df58-7b9f-ff7e-d57a2e416fb9",
                        "data_type": "SERIES",
                        "name": "x_indices",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
                    "connector": {
                        "id": "829cbd05-7a33-c931-b16e-a105f9a7c885",
                        "data_type": "SERIES",
                        "name": "x",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 18
            {
                "id": "c0d9a49c-3fbf-4ef5-88fa-690d17b9ce02",
                "start": {
                    "operator": "74608f8a-d973-4add-9764-ad3348b3bb57",
                    "connector": {
                        "id": "0e368818-fdfb-6796-a463-8bd9d5ff03e5",
                        "data_type": "SERIES",
                        "name": "y_indices",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "end": {
                    "operator": "e362967a-fa2d-4d7c-8ef9-e58eceb45e2b",
                    "connector": {
                        "id": "54e9008c-0451-9e1c-c334-31e3887a4b07",
                        "data_type": "SERIES",
                        "name": "y",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 19 from constant input to operator
            {
                "id": "c00048d3-2371-465b-a8f8-bd1e928b7576",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "a062167b-8fe0-4a48-bd94-552039a4f7af",
                        "data_type": "STRING",
                        "name": "column_name",
                        "position": {"y": 0, "x": -200},
                        "value": "y",
                    },
                },
                "end": {
                    "operator": "2ae1a251-3d86-4323-ae64-0702cfb5a4cf",
                    "connector": {
                        "id": "fc417e48-f7d8-0bbf-60ac-af92a9150170",
                        "data_type": "STRING",
                        "name": "column_name",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 20 from constant input to operator
            {
                "id": "bc075299-15f7-44b7-b29e-543248cf339a",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "088d81cf-caa3-4fd4-ab7a-e1538de3b559",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": -200},
                        "value": "y",
                    },
                },
                "end": {
                    "operator": "1ecddb98-6ae1-48b0-b125-20d3b4e3118c",
                    "connector": {
                        "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
            # 21 from constant input to operator
            {
                "id": "bd6009f8-c766-434a-a316-9f2dcd44704e",
                "start": {
                    "operator": None,
                    "connector": {
                        "id": "d4ee291f-4476-447d-a161-a6b16fdaf205",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": -200},
                        "value": "x",
                    },
                },
                "end": {
                    "operator": "177db51b-6a68-4808-8e09-1a6d87f3e579",
                    "connector": {
                        "id": "44d0fd6a-4f72-3ec1-d5dc-4f8df7029652",
                        "data_type": "STRING",
                        "name": "name",
                        "position": {"y": 0, "x": 0},
                    },
                },
                "path": [],
            },
        ],
        "inputs": [
            # 0
            {
                "id": "8a569d4a-863a-4800-abb5-819cc1e8a030",
                "data_type": "INT",
                "name": "n_estimators",
                "position": {"y": 240, "x": 940},
            },
            # 1
            {
                "id": "b817a8f6-764d-4003-96c4-b8ba52981fb1",
                "data_type": "INT",
                "name": "n_grid",
                "position": {"y": 90, "x": -60},
            },
            # 2
            {
                "id": "f468e81c-0e8f-4869-a268-892a391327d6",
                "data_type": "FLOAT",
                "name": "x_max",
                "position": {"y": 120, "x": -60},
            },
            # 3
            {
                "id": "d5c0c6b6-3b9d-48ed-9c40-70ecf14a3d0d",
                "data_type": "FLOAT",
                "name": "x_min",
                "position": {"y": 150, "x": -60},
            },
            # 4
            {
                "id": "196c78f4-6b9a-4476-9b37-ec80986a6a47",
                "data_type": "SERIES",
                "name": "x_vals",
                "position": {"y": 520, "x": -50},
            },
            # 5
            {
                "id": "1cabf944-d63e-4d0d-a1e7-d6c0ffb193c5",
                "data_type": "FLOAT",
                "name": "y_max",
                "position": {"y": 180, "x": -60},
            },
            # 6
            {
                "id": "2c212317-15a7-4599-b1f2-b6333a6c7a2b",
                "data_type": "FLOAT",
                "name": "y_min",
                "position": {"y": 210, "x": -60},
            },
            # 7
            {
                "id": "1c3224e0-90e6-4d03-9160-3a9417c27841",
                "data_type": "SERIES",
                "name": "y_vals",
                "position": {"y": 370, "x": -50},
            },
        ],
        "constants": [
            # 1
            {
                "id": "a062167b-8fe0-4a48-bd94-552039a4f7af",
                "data_type": "STRING",
                "position": {"y": 0, "x": -200},
                "value": "y",
            },
            # 2
            {
                "id": "088d81cf-caa3-4fd4-ab7a-e1538de3b559",
                "data_type": "STRING",
                "position": {"y": 0, "x": -200},
                "value": "y",
            },
            # 3
            {
                "id": "d4ee291f-4476-447d-a161-a6b16fdaf205",
                "data_type": "STRING",
                "position": {"y": 0, "x": -200},
                "value": "x",
            },
        ],
        "outputs": [
            {
                "id": "5dcdf141-590f-42d6-86bd-460af86147a7",
                "data_type": "PLOTLYJSON",
                "name": "contour_plot",
                "position": {"y": -100, "x": 2010},
            }
        ],
    },
    "test_wiring": {
        "id": "2634db74-157b-4c07-a49d-6aedc6f9a7bc",
        "name": "STANDARD-WIRING",
        "input_wirings": [
            {
                "id": "2ff1b365-0e29-4253-bfa0-a1474f2fb2cd",
                "workflow_input_name": "x_vals",
                "adapter_id": "direct_provisioning",
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
                "workflow_input_name": "y_vals",
                "adapter_id": "direct_provisioning",
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
                "workflow_input_name": "n_estimators",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 100},
            },
            {
                "id": "93292699-90f1-41ec-b11c-4538521a64f0",
                "workflow_input_name": "n_grid",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 30},
            },
            {
                "id": "1aedec9f-9c37-4894-b462-c787c9ec8593",
                "workflow_input_name": "x_max",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 3},
            },
            {
                "id": "327ddb6a-f21c-4c2c-a3a0-cfd3105c3015",
                "workflow_input_name": "x_min",
                "adapter_id": "direct_provisioning",
                "filters": {"value": -3},
            },
            {
                "id": "0de8335d-b104-4ca4-b0fc-4066eb1f3ae6",
                "workflow_input_name": "y_max",
                "adapter_id": "direct_provisioning",
                "filters": {"value": 3},
            },
            {
                "id": "552a8f95-9e8f-474b-b28c-652ae26ab1c2",
                "workflow_input_name": "y_min",
                "adapter_id": "direct_provisioning",
                "filters": {"value": -3},
            },
        ],
        "output_wirings": [
            {
                "id": "4c6034e9-1f58-4b98-b6a5-68231a41e08a",
                "workflow_output_name": "contour_plot",
                "adapter_id": "direct_provisioning",
            },
            {
                "id": "d01005c7-552c-48a4-972c-28cd7044597a",
                "workflow_output_name": "xs",
                "adapter_id": "direct_provisioning",
            },
        ],
    },
}

valid_component_dto_dict = {
    "category": "Arithmetic",
    "code": "",
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
    "wirings": [],
}


def test_tr_validators_accept_valid_released_tr():
    TransformationRevision(**tr_json_valid_released_example)


def test_tr_validator_content_type_correct():
    id = get_uuid_from_seed("test")

    combi = namedtuple("combi", "type content")
    incorrect_combis = (
        combi(type=Type.WORKFLOW, content="test"),
        combi(type=Type.COMPONENT, content=WorkflowContent()),
    )

    correct_combis = (
        combi(type=Type.WORKFLOW, content=WorkflowContent()),
        combi(type=Type.COMPONENT, content="test"),
    )

    for combi in incorrect_combis:
        with pytest.raises(ValidationError):
            TransformationRevision(
                id=id,
                revision_group_id=id,
                name="Test",
                description="Test description",
                version_tag="1.0.0",
                category="Test category",
                state=State.DRAFT,
                type=combi.type,
                content=combi.content,
                io_interface=IOInterface(),
                test_wiring=WorkflowWiring(),
                documentation="",
            )
    for combi in correct_combis:
        # no validation errors
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Test",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=combi.type,
            content=combi.content,
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )


def test_tr_validator_version_tag_not_latest():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Test",
            description="Test description",
            version_tag="latest",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_regex_validator_not_whitelisted_character():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="+",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_validstr_regex_validator_empty():
    id = get_uuid_from_seed("test")
    TransformationRevision(
        id=id,
        revision_group_id=id,
        name="Test",
        description="",
        version_tag="1.0.0",
        category="Test category",
        state=State.DRAFT,
        type=Type.COMPONENT,
        content="test",
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        documentation="",
    )

def test_tr_nonemptyvalidstr_regex_validator_empty():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_validator_max_characters():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Name Name Name Name Name Name Name Name Name Name Name Name Name",
            description="Test description",
            version_tag="1.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_shortnonemptyvalidstr_validator_max_characters():
    id = get_uuid_from_seed("test")
    with pytest.raises(ValidationError):
        TransformationRevision(
            id=id,
            revision_group_id=id,
            name="Name",
            description="Test description",
            version_tag="1.0.0.0.0.0.0.0.0.0.0",
            category="Test category",
            state=State.DRAFT,
            type=Type.COMPONENT,
            content="test",
            io_interface=IOInterface(),
            test_wiring=WorkflowWiring(),
            documentation="",
        )

def test_tr_nonemptyvalidstr_regex_validator_fancy_characters():
    id = get_uuid_from_seed("test")
    TransformationRevision(
        id=id,
        revision_group_id=id,
        name="bößä",
        description="中文, español, Çok teşekkürler",
        version_tag="(-_-) /  =.=",
        category="ไทย",
        state=State.DRAFT,
        type=Type.COMPONENT,
        content="test",
        io_interface=IOInterface(),
        test_wiring=WorkflowWiring(),
        documentation="",
    )

def test_tr_validator_io_interface_fits_to_content():
    tr_json_empty_io_interface = deepcopy(tr_json_valid_released_example)
    tr_json_empty_io_interface["io_interface"]["inputs"] = []
    tr_json_empty_io_interface["io_interface"]["outputs"] = []
    tr_generated_io_interface = TransformationRevision(**tr_json_empty_io_interface)

    assert len(tr_generated_io_interface.content.inputs) == len(
        tr_json_valid_released_example["io_interface"]["inputs"]
    )


def test_wrap_component_in_tr_workflow():
    component_dto = ComponentRevisionFrontendDto(**valid_component_dto_dict)
    tr_component = component_dto.to_transformation_revision()

    tr_workflow = tr_component.wrap_component_in_tr_workflow()

    assert valid_component_dto_dict["name"] == tr_workflow.name
    assert valid_component_dto_dict["category"] == tr_workflow.category
    assert valid_component_dto_dict["tag"] == tr_workflow.version_tag
    assert valid_component_dto_dict["state"] == tr_workflow.state
    assert Type.WORKFLOW == tr_workflow.type
    assert 1 == len(tr_workflow.content.operators)
    assert valid_component_dto_dict["id"] == str(
        tr_workflow.content.operators[0].transformation_id
    )
    assert len(valid_component_dto_dict["inputs"]) == len(
        tr_workflow.content.operators[0].inputs
    )
    assert len(valid_component_dto_dict["outputs"]) == len(
        tr_workflow.content.operators[0].outputs
    )
    assert len(tr_component.io_interface.inputs) == len(tr_workflow.io_interface.inputs)
    assert len(tr_component.io_interface.outputs) == len(
        tr_workflow.io_interface.outputs
    )


def test_to_workflow_node():
    component_dto = ComponentRevisionFrontendDto(**valid_component_dto_dict)
    tr_component = component_dto.to_transformation_revision()
    tr_workflow = tr_component.wrap_component_in_tr_workflow()
    nested_transformations = {tr_workflow.content.operators[0].id: tr_component}

    workflow_node = tr_workflow.to_workflow_node(
        uuid4(), nested_nodes(tr_workflow, nested_transformations)
    )

    assert len(workflow_node.inputs) == len(valid_component_dto_dict["inputs"])
    assert len(workflow_node.outputs) == len(valid_component_dto_dict["outputs"])
    assert len(workflow_node.sub_nodes) == 1
    assert len(workflow_node.connections) == 0
    assert workflow_node.name == valid_component_dto_dict["name"]
