from copy import deepcopy

import pytest

from hetdesrun.persistence.models.operator import Operator

operator_dict = {
    "id": "f2e74579-6058-474a-bb9e-ae2d9a059b6d",
    "inputs": [
        {
            "data_type": "SERIES",
            "id": "15637612-6dc7-4f55-7b5b-83c9fdac8579",
            "name": "series",
            "position": {"x": 0, "y": 0},
            "type": "REQUIRED",
            "value": None,
            "exposed": True,
        },
        {
            "data_type": "ANY",
            "id": "3e68b069-390e-cf1f-5916-101b7fe4cf4a",
            "name": "series_or_dataframe",
            "position": {"x": 0, "y": 0},
            "type": "REQUIRED",
            "value": None,
            "exposed": True,
        },
    ],
    "name": "Combine into DataFrame",
    "outputs": [
        {
            "data_type": "DATAFRAME",
            "id": "cbf856b7-faf7-3079-d8e8-3b666d6f9d84",
            "name": "dataframe",
            "position": {"x": 0, "y": 0},
        }
    ],
    "position": {"x": 250, "y": 130},
    "revision_group_id": "68f91351-a1f5-9959-414a-2c72003f3226",
    "state": "RELEASED",
    "transformation_id": "68f91351-a1f5-9959-414a-2c72003f3226",
    "type": "COMPONENT",
    "version_tag": "1.0.0",
}


def test_operator_accepted() -> None:
    Operator(**operator_dict)


def test_operator_validator_is_not_draft() -> None:
    draft_operator_dict = deepcopy(operator_dict)
    draft_operator_dict["state"] = "DRAFT"
    with pytest.raises(ValueError, match=r"Operator.* has state"):
        Operator(**draft_operator_dict)
