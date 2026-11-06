import json
from copy import deepcopy
from typing import Any
from unittest import mock
from urllib.parse import quote

import pytest

from hetdesrun.models.adapter_data import RefIdType
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


@pytest.mark.parametrize("adapter_id", ["drop", "plot"])
def test_output_wiring_metadata_type_without_additional_fields_accepted_for_drop_and_plot(
    adapter_id: str,
) -> None:
    # Switching a metadata output wiring to "Drop Result" or "Plot" in the frontend
    # can leave the metadata type behind while ref_id and ref_key are reset.
    output_wiring = OutputWiring(
        workflow_output_name="wf_output",
        adapter_id=adapter_id,
        ref_id_type="THINGNODE",
        type="metadata(any)",
    )
    assert output_wiring.adapter_id == adapter_id


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


def uri_wiring(
    wiring_class: type[InputWiring] | type[OutputWiring], uri: str, **fields: Any
) -> InputWiring | OutputWiring:
    name_field = "workflow_input_name" if wiring_class is InputWiring else "workflow_output_name"
    return wiring_class(**{name_field: "wf_io", "uri": uri, **fields})


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
def test_uri_fragment_sets_ref_key_and_ref_id_type(
    wiring_class: type[InputWiring] | type[OutputWiring],
) -> None:
    # "+" and spaces in the ref key must survive url encoding
    ref_key = "C - 2023-02-14 12:19:38+00:00"
    wiring = uri_wiring(
        wiring_class,
        f"hd://blob-storage-adapter/i-i/C#ref_key={quote(ref_key, safe='')}&ref_id_type=THINGNODE",
    )

    assert wiring.adapter_id == "blob-storage-adapter"
    assert wiring.ref_id == "i-i/C"
    assert wiring.ref_key == ref_key
    assert wiring.ref_id_type == RefIdType.THINGNODE


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
def test_uri_query_filters_and_fragment_both_applied(
    wiring_class: type[InputWiring] | type[OutputWiring],
) -> None:
    wiring = uri_wiring(wiring_class, "hd://sql-adapter/tbl?x=1&y=2#ref_key=abc&ref_id_type=SOURCE")

    assert wiring.filters == {"x": "1", "y": "2"}
    assert wiring.ref_key == "abc"
    assert wiring.ref_id_type == RefIdType.SOURCE


@pytest.mark.parametrize(
    ("wiring_class", "wiring_dict"),
    [
        (InputWiring, blob_adapter_input_wiring_dict),
        (OutputWiring, blob_adapter_output_wiring_dict),
    ],
)
def test_uri_metadata_wiring_equals_wiring_from_fields(
    wiring_class: type[InputWiring] | type[OutputWiring], wiring_dict: dict
) -> None:
    uri = (
        f"hd://{wiring_dict['adapter_id']}/{wiring_dict['ref_id']}"
        f"#ref_key={quote(wiring_dict['ref_key'], safe='')}"
        f"&ref_id_type={wiring_dict['ref_id_type']}"
    )
    wiring_from_uri = uri_wiring(wiring_class, uri, type=wiring_dict["type"])
    wiring_from_fields = wiring_class(**wiring_dict)

    not_compared = {"uri", "workflow_input_name", "workflow_output_name"}
    assert wiring_from_uri.model_dump(exclude=not_compared) == wiring_from_fields.model_dump(
        exclude=not_compared
    )


def test_uri_fragment_sets_attrs_and_use_default_value() -> None:
    attrs = {"dataset_metadata": {"name": "x"}, "metrics": [1, 2]}
    encoded_attrs = quote(json.dumps(attrs), safe="")
    wiring = InputWiring(
        workflow_input_name="wf_io",
        uri=f"hd://sql-adapter/tbl#attrs={encoded_attrs}&use_default_value=true",
    )

    assert wiring.attrs == attrs
    assert wiring.use_default_value is True


def test_uri_fragment_attrs_and_use_default_value_ignored_for_output_wiring() -> None:
    wiring = uri_wiring(
        OutputWiring,
        f"hd://sql-adapter/tbl#attrs={quote(json.dumps({'a': 1}), safe='')}&use_default_value=true",
    )

    assert not hasattr(wiring, "attrs")
    assert not hasattr(wiring, "use_default_value")


def test_uri_fragment_overrides_wiring_fields() -> None:
    wiring = InputWiring(
        workflow_input_name="wf_io",
        uri="hd://sql-adapter/tbl#ref_key=new&use_default_value=false",
        ref_key="old",
        use_default_value=True,
    )

    assert wiring.ref_key == "new"
    assert wiring.use_default_value is False


def test_uri_query_keys_named_like_fragment_fields_are_filters() -> None:
    wiring = InputWiring(
        workflow_input_name="wf_io", uri="hd://sql-adapter/tbl?ref_key=x#ref_id_type=SOURCE"
    )

    assert wiring.filters == {"ref_key": "x"}
    assert wiring.ref_key is None
    assert wiring.ref_id_type == RefIdType.SOURCE


@pytest.mark.parametrize(
    ("fragment", "error_match"),
    [
        ("refkey=abc", "Extra inputs are not permitted"),
        ("ref_key=a&ref_key=b", r"\['ref_key'\] more than once"),
        ("ref_id_type=PLANT", "Input should be 'SOURCE', 'SINK' or 'THINGNODE'"),
        ("attrs=" + quote("{broken", safe=""), "attrs is not valid json"),
        ("attrs=" + quote("[1, 2]", safe=""), "Input should be a valid dictionary"),
    ],
)
def test_uri_fragment_invalid(fragment: str, error_match: str) -> None:
    with pytest.raises(ValueError, match=error_match):
        uri_wiring(InputWiring, f"hd://sql-adapter/tbl#{fragment}")


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
def test_uri_overrides_explicit_fields_only_where_present(
    wiring_class: type[InputWiring] | type[OutputWiring],
) -> None:
    overridden = uri_wiring(
        wiring_class, "hd://component-adapter/new", adapter_id="sql-adapter", ref_id="old"
    )
    assert overridden.adapter_id == "component-adapter"
    assert overridden.ref_id == "new"

    # a uri without path does not provide a ref_id
    kept = uri_wiring(wiring_class, "hd://sql-adapter", ref_id="kept")
    assert kept.adapter_id == "sql-adapter"
    assert kept.ref_id == "kept"


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
def test_uri_metadata_wiring_with_explicit_adapter_id(
    wiring_class: type[InputWiring] | type[OutputWiring],
) -> None:
    # ref_key and ref_id_type are only provided by the uri, so the metadata type
    # must be checked after the uri expansion.
    wiring = uri_wiring(
        wiring_class,
        "hd://blob-storage-adapter/i-i/C#ref_key=C&ref_id_type=THINGNODE",
        adapter_id="blob-storage-adapter",
        type="metadata(any)",
    )

    assert wiring.ref_key == "C"
    assert wiring.ref_id_type == RefIdType.THINGNODE


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
def test_uri_wiring_with_explicit_adapter_id_and_null_ref_id(
    wiring_class: type[InputWiring] | type[OutputWiring],
) -> None:
    # Clients serializing all fields send ref_id null although the uri provides it
    wiring = uri_wiring(wiring_class, "hd://sql-adapter/tbl", adapter_id="sql-adapter", ref_id=None)

    assert wiring.ref_id == "tbl"


@pytest.mark.parametrize("wiring_class", [InputWiring, OutputWiring])
@pytest.mark.parametrize(
    ("uri", "fields", "error_match"),
    [
        (
            "hd://sql-adapter/n#ref_id_type=THINGNODE",
            {"adapter_id": "sql-adapter", "type": "metadata(any)"},
            "requires additional fields",
        ),
        (
            "hd://sql-adapter/n#ref_id_type=THINGNODE",
            {"type": "metadata(any)"},
            "requires additional fields",
        ),
        ("hd://sql-adapter", {"adapter_id": "sql-adapter"}, "ref_id must be provided"),
        ("hd://sql-adapter", {}, "ref_id must be provided"),
    ],
)
def test_uri_wiring_incomplete_after_uri_expansion_rejected(
    wiring_class: type[InputWiring] | type[OutputWiring],
    uri: str,
    fields: dict[str, Any],
    error_match: str,
) -> None:
    with pytest.raises(ValueError, match=error_match):
        uri_wiring(wiring_class, uri, **fields)
