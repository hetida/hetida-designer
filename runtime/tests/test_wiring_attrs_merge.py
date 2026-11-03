import uuid
from copy import deepcopy

import pandas as pd
from hdhelpers.metadata import META_KEY, attach_metadata

from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.adapters.virtual_structure_adapter.utils import (
    add_vst_metadata_to_input_wiring_attrs,
)
from hetdesrun.models.wiring import InputWiring
from hetdesrun.structure.models import StructureServiceSource
from hetdesrun.utils import deep_merge
from hetdesrun.wiring import update_with_metadata_from_input_wiring

LOADED_ATTRS = {
    "dataset_metadata": {
        "metric_key": "id",
        "queried_metrics": ["a"],
        "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
        "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
        "ref_interval_type": "closed",
    },
    "metrics": [{"id": "a", "name": "A", "value_dimensions": []}],
}


def test_deep_merge() -> None:
    base = {"a": {"b": 1, "c": {"d": 2}}, "e": [1, 2], "f": 3}
    update = {"a": {"c": {"g": 4}, "h": 5}, "e": [3], "f": {"i": 6}}
    base_before, update_before = deepcopy(base), deepcopy(update)

    merged = deep_merge(base, update)

    assert merged == {"a": {"b": 1, "c": {"d": 2, "g": 4}, "h": 5}, "e": [3], "f": {"i": 6}}
    # neither base nor update are changed and the result shares nothing with them
    assert (base, update) == (base_before, update_before)
    merged["a"]["c"]["d"] = 0
    merged["e"].append(4)
    merged["f"]["i"] = 0
    assert (base, update) == (base_before, update_before)


def input_wiring_with_attrs(attrs: dict | None) -> InputWiring:
    return InputWiring(
        workflow_input_name="inp", adapter_id="demo-adapter-python", ref_id="a", attrs=attrs
    )


def test_input_wiring_attrs_are_merged_recursively() -> None:
    series = pd.Series([1.0, 2.0])
    series.attrs = deepcopy(LOADED_ATTRS)
    wiring_attrs = {
        "dataset_metadata": {"default_timezone": "Europe/Berlin"},
        "metrics": [{"id": "a", "name": "A from wiring", "value_dimensions": []}],
    }
    input_wiring = input_wiring_with_attrs(wiring_attrs)
    attrs_object = series.attrs

    update_with_metadata_from_input_wiring(series, input_wiring)

    # a single field of the dataset metadata is added, lists like the metrics are replaced
    assert series.attrs == {
        "dataset_metadata": LOADED_ATTRS["dataset_metadata"]
        | {"default_timezone": "Europe/Berlin"},
        "metrics": [{"id": "a", "name": "A from wiring", "value_dimensions": []}],
    }
    assert series.attrs is attrs_object
    # the attrs of the loaded object share nothing with the input wiring
    series.attrs["dataset_metadata"]["default_timezone"] = "UTC"
    series.attrs["metrics"][0]["name"] = "changed"
    assert input_wiring.attrs == wiring_attrs


def test_input_wiring_attrs_are_merged_into_the_json_form_of_attached_metadata() -> None:
    loaded_attrs = deepcopy(LOADED_ATTRS)
    loaded_attrs["dataset_metadata"]["single_metric"] = "a"
    loaded_attrs["metrics"][0]["value_dimensions"] = [
        {"column": "value", "unit": None, "measurement": None}
    ]
    series = pd.Series([1.0, 2.0])
    series.attrs = deepcopy(loaded_attrs) | {"other": 1}
    assert attach_metadata(series, "SERIES") is not None

    update_with_metadata_from_input_wiring(
        series, input_wiring_with_attrs({"dataset_metadata": {"default_timezone": "Europe/Berlin"}})
    )

    # as plain attrs, which are parsed again when attaching the metadata of the inputs
    assert series.attrs == {
        "dataset_metadata": loaded_attrs["dataset_metadata"]
        | {"default_timezone": "Europe/Berlin"},
        "metrics": loaded_attrs["metrics"],
        "other": 1,
    }
    assert META_KEY not in series.attrs


def test_vst_metadata_is_merged_into_input_wiring_attrs() -> None:
    meta_data = {
        "dataset_metadata": {"default_timezone": "Europe/Berlin", "ref_data_frequency": "1h"}
    }
    source = StructureServiceSource(
        external_id="src",
        stakeholder_key="stk",
        name="a source",
        type=ExternalType.TIMESERIES_FLOAT,
        adapter_key="demo-adapter-python",
        source_id="src_id",
        meta_data=meta_data,
    )
    input_wirings = [
        input_wiring_with_attrs(
            {"dataset_metadata": {"default_timezone": "UTC", "query_timestamp": "x"}, "other": 1}
        ),
        input_wiring_with_attrs(None),
    ]

    other_source = source.model_copy(update={"id": uuid.uuid4()})

    add_vst_metadata_to_input_wiring_attrs(
        input_wirings, [0, 1], {source.id: source, other_source.id: other_source}
    )

    # the meta_data of the virtual source takes precedence
    assert input_wirings[0].attrs == {
        "dataset_metadata": {
            "default_timezone": "Europe/Berlin",
            "query_timestamp": "x",
            "ref_data_frequency": "1h",
        },
        "other": 1,
    }
    assert input_wirings[1].attrs == meta_data
    # the input wirings share nothing with the virtual source
    assert input_wirings[1].attrs is not None
    input_wirings[1].attrs["dataset_metadata"]["ref_data_frequency"] = "1D"
    assert source.meta_data == {
        "dataset_metadata": {"default_timezone": "Europe/Berlin", "ref_data_frequency": "1h"}
    }
