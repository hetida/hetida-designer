from copy import deepcopy
from unittest import mock

import pytest

from hetdesrun.models.wiring import (
    InputWiring,
    OutputWiring,
    WorkflowWiring,
)

direct_provisioning_input_wiring_dict = {
    "adapter_id": 1,
    "workflow_input_name": "wf_input",
}

direct_provisioning_output_wiring_dict = {
    "adapter_id": 1,
    "workflow_output_name": "wf_output",
}

blob_adapter_input_wiring_dict = {
    "adapter_id": "blob-storage-adapter",
    "filters": {},
    "ref_id": "i-i/C",
    "ref_id_type": "THINGNODE",
    "ref_key": "C - 2023-02-14 12:19:38+00:00",
    "type": "metadata(any)",
    "workflow_input_name": "class_entity",
}

blob_adapter_output_wiring_dict = {
    "adapter_id": "blob-storage-adapter",
    "ref_id": "i-i/C",
    "ref_id_type": "THINGNODE",
    "ref_key": "C - Next Object",
    "type": "metadata(any)",
    "workflow_output_name": "class_entity",
}

workflow_wiring_dict = {
    "input_wirings": [
        direct_provisioning_input_wiring_dict,
        blob_adapter_input_wiring_dict,
    ],
    "output_wirings": [
        direct_provisioning_output_wiring_dict,
        blob_adapter_output_wiring_dict,
    ],
}


def test_output_wiring_accepted() -> None:
    OutputWiring(**direct_provisioning_output_wiring_dict)
    OutputWiring(**blob_adapter_output_wiring_dict)


def test_output_wiring_validator_adapter_id_known() -> None:
    output_wiring_with_unknown_adapter_id_dict = deepcopy(direct_provisioning_output_wiring_dict)
    output_wiring_with_unknown_adapter_id_dict["adapter_id"] = 23
    with (
        mock.patch("hetdesrun.models.wiring.ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS", False),
        pytest.raises(ValueError, match="not known"),
    ):
        OutputWiring(**output_wiring_with_unknown_adapter_id_dict)


def test_output_wiring_validator_name_valid_python_identifier() -> None:
    output_wiring_with_invalid_name_dict = deepcopy(direct_provisioning_output_wiring_dict)
    output_wiring_with_invalid_name_dict["workflow_output_name"] = "invalid identifier"
    with pytest.raises(ValueError, match="not a valid Python identifier"):
        OutputWiring(**output_wiring_with_invalid_name_dict)


def test_output_wiring_validator_metadata_type_includes_addtional_fields() -> None:
    output_wiring_missing_additional_metadata_fields = deepcopy(blob_adapter_output_wiring_dict)
    del output_wiring_missing_additional_metadata_fields["ref_key"]
    with pytest.raises(ValueError, match="requires additional fields"):
        OutputWiring(**output_wiring_missing_additional_metadata_fields)


def test_output_wiring_validator_no_reserved_filter_keys() -> None:
    output_wiring_with_reserved_filter_keys_dict = deepcopy(direct_provisioning_output_wiring_dict)
    output_wiring_with_reserved_filter_keys_dict["filters"] = {"to": "somewhere"}
    with pytest.raises(ValueError, match="reserved filter keys"):
        OutputWiring(**output_wiring_with_reserved_filter_keys_dict)


def test_output_wiring_validator_none_filter_value_to_empty_string() -> None:
    output_wiring_with_none_filter_value_dict = deepcopy(direct_provisioning_output_wiring_dict)
    output_wiring_with_none_filter_value_dict["filters"] = {"key": None}
    input_wiring_with_empty_string_filter_value = OutputWiring(
        **output_wiring_with_none_filter_value_dict
    )

    assert input_wiring_with_empty_string_filter_value.filters["key"] == ""


def test_input_wiring_accepted() -> None:
    InputWiring(**direct_provisioning_input_wiring_dict)
    InputWiring(**blob_adapter_input_wiring_dict)


def test_input_wiring_validator_adapter_id_known() -> None:
    input_wiring_with_unknown_adapter_id_dict = deepcopy(direct_provisioning_input_wiring_dict)
    input_wiring_with_unknown_adapter_id_dict["adapter_id"] = 23
    with (
        mock.patch("hetdesrun.models.wiring.ALLOW_UNCONFIGURED_ADAPTER_IDS_IN_WIRINGS", False),
        pytest.raises(ValueError, match="not known"),
    ):
        InputWiring(**input_wiring_with_unknown_adapter_id_dict)


def test_input_wiring_validator_name_valid_python_identifier() -> None:
    input_wiring_with_invalid_name_dict = deepcopy(direct_provisioning_input_wiring_dict)
    input_wiring_with_invalid_name_dict["workflow_input_name"] = "invalid identifier"
    with pytest.raises(ValueError, match="not a valid Python identifier"):
        InputWiring(**input_wiring_with_invalid_name_dict)


def test_input_wiring_validator_metadata_type_includes_addtional_fields() -> None:
    input_wiring_missing_additional_metadata_fields_dict = deepcopy(blob_adapter_input_wiring_dict)
    del input_wiring_missing_additional_metadata_fields_dict["ref_key"]
    with pytest.raises(ValueError, match="requires additional fields"):
        InputWiring(**input_wiring_missing_additional_metadata_fields_dict)


def test_input_wiring_validator_no_reserved_filter_keys() -> None:
    input_wiring_with_reserved_filter_keys_dict = deepcopy(direct_provisioning_input_wiring_dict)
    input_wiring_with_reserved_filter_keys_dict["filters"] = {"from": "home"}
    with pytest.raises(ValueError, match="reserved filter keys"):
        InputWiring(**input_wiring_with_reserved_filter_keys_dict)


def test_input_wiring_validator_none_filter_value_to_empty_string() -> None:
    input_wiring_with_none_filter_value_dict = deepcopy(direct_provisioning_input_wiring_dict)
    input_wiring_with_none_filter_value_dict["filters"] = {"key": None}
    input_wiring_with_empty_string_filter_value = InputWiring(
        **input_wiring_with_none_filter_value_dict
    )

    assert input_wiring_with_empty_string_filter_value.filters["key"] == ""


def test_workflow_wiring_accepted() -> None:
    WorkflowWiring(**workflow_wiring_dict)


def test_workflow_wiring_validator_input_names_unique() -> None:
    workflow_wiring_with_not_unique_inputs_dict = deepcopy(workflow_wiring_dict)
    workflow_wiring_with_not_unique_inputs_dict["input_wirings"][0]["workflow_input_name"] = (
        workflow_wiring_with_not_unique_inputs_dict["input_wirings"][1]["workflow_input_name"]
    )
    with pytest.raises(ValueError, match=r"Duplicates.* not allowed"):
        WorkflowWiring(**workflow_wiring_with_not_unique_inputs_dict)


def test_workflow_wiring_validator_output_names_unique() -> None:
    workflow_wiring_with_not_unique_outputs_dict = deepcopy(workflow_wiring_dict)
    workflow_wiring_with_not_unique_outputs_dict["output_wirings"][0]["workflow_output_name"] = (
        workflow_wiring_with_not_unique_outputs_dict["output_wirings"][1]["workflow_output_name"]
    )
    with pytest.raises(ValueError, match=r"Duplicates.* not allowed"):
        WorkflowWiring(**workflow_wiring_with_not_unique_outputs_dict)
