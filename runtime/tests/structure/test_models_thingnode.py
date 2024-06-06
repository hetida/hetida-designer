import uuid
from copy import deepcopy

import pytest
from pydantic import ValidationError

from hetdesrun.structure.models import ThingNode

valid_example_tn_dict = {
    "id": 9999,
    "name": "Name",
    "element_type_id": 1,
    "entity_uuid": str(uuid.uuid4()),
}


def test_thingnode_accepted() -> None:
    ThingNode(**valid_example_tn_dict)


def test_operator_validator_is_not_draft() -> None:
    invalid_example_tn_dict = deepcopy(valid_example_tn_dict)
    invalid_example_tn_dict["id"] = "not an integer"
    with pytest.raises(ValidationError, match="id\n  value is not a valid integer"):
        ThingNode(**invalid_example_tn_dict)
