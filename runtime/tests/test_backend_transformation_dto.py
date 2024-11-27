from copy import deepcopy

import pytest

from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto

valid_transformation = {
    "id": "7c42e11e-7ca8-416a-9eae-fb3f24d54b70",
    "groupId": "919dfb8a-e812-437b-9c6d-9d96a5e90843",
    "name": "One Class Support Vector Machine",
    "description": "Compoment for learning how to work with hetida designer",
    "category": "Anomaly Detection",
    "type": "COMPONENT",
    "state": "DRAFT",
    "tag": "1.0.3 Copy",
    "inputs": [
        {
            "id": "5541a998-9d23-44a5-8375-5bf053a91bc0",
            "type": "FLOAT",
            "name": "nu",
            "posY": 0,
            "posX": 0,
        },
        {
            "id": "06b2b26c-b91d-4256-b171-3b536752c54c",
            "type": "DATAFRAME",
            "name": "test_data",
            "posY": 0,
            "posX": 0,
        },
        {
            "id": "2a51557c-b38a-4ffc-ad48-c8e2f881f369",
            "type": "DATAFRAME",
            "name": "train_data",
            "posY": 0,
            "posX": 0,
        },
    ],
    "outputs": [
        {
            "id": "76bc5f44-e3fa-4fea-b46e-74d41353278f",
            "type": "SERIES",
            "name": "decision_function_labels",
            "posY": 0,
            "posX": 0,
        },
        {
            "id": "082121b3-7c6c-46a2-838d-1455fff9e27a",
            "type": "ANY",
            "name": "trained_model",
            "posY": 0,
            "posX": 0,
        },
    ],
    "code": "",
    "wirings": [],
}


def test_transformation_validators_accept_valid_workflow():
    TransformationRevisionFrontendDto(**valid_transformation)


def test_transformation_validator_input_names_unique_identifies_double_name():
    transformation_with_double_input_name = deepcopy(valid_transformation)
    transformation_with_double_input_name["inputs"][1]["name"] = (
        transformation_with_double_input_name["inputs"][0]["name"]
    )

    with pytest.raises(ValueError) as exc:  # noqa: PT011
        TransformationRevisionFrontendDto(**transformation_with_double_input_name)

    assert "duplicates" in str(exc.value)


def test_transformation_validator_output_names_unique_identifies_double_name():
    transformation_with_double_output_name = deepcopy(valid_transformation)
    transformation_with_double_output_name["outputs"][1]["name"] = (
        transformation_with_double_output_name["outputs"][0]["name"]
    )

    with pytest.raises(ValueError) as exc:  # noqa: PT011
        TransformationRevisionFrontendDto(**transformation_with_double_output_name)

    assert "duplicates" in str(exc.value)


def test_transformation_dto_to_transformation_revision():
    transformation_revision = TransformationRevisionFrontendDto(
        **valid_transformation
    ).to_transformation_revision()

    assert len(transformation_revision.io_interface.inputs) == len(valid_transformation["inputs"])
    assert len(transformation_revision.io_interface.outputs) == len(valid_transformation["outputs"])


def test_transformation_dto_from_transformation_revision():
    transformation_revision = TransformationRevisionFrontendDto(
        **valid_transformation
    ).to_transformation_revision()
    transformation_revision_dto = TransformationRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )

    assert len(transformation_revision_dto.inputs) == len(valid_transformation["inputs"])
    assert len(transformation_revision_dto.outputs) == len(valid_transformation["outputs"])
