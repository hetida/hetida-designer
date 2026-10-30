"""Documentation for Add/Update Attributes (SingleTSFrame)

# Add/Update Attributes (SingleTSFrame)

## Description
Add attributes to a SingleTSFrame or update attributes of a SingleTSFrame.
If you wish to attach metadata to a SingleTSFrame, please follow the conventions outlined in the [documentation](https://hetida.github.io/hetida-designer/user_guide/attached_metadata/).

## Inputs
* **singletsframe** (SingleTSFrame): The input SingleTSFrame.
* **attributes** (Any): A dictionary with string keys to be added to the input SingleTSFrame.

## Outputs
* **singletsframe** (SingleTSFrame): The input singletsframe with added attributes.

## Details
Adds attributes to a SingleTSFrame. Adding an attribute with a key, that is already included in the attributes of the singletsframe, will update the corresponding value. Metadata following the metadata conventions is updated in its JSON form, e.g. providing "dataset_metadata" replaces the complete dataset metadata. Afterwards it is attached to the result as model again, if it still follows the metadata conventions. The input singletsframe itself is not changed.

**Note:** Selecting "Only Output" for the output singletsframe means that it is wired to the "direct provisioning" adapter, which sends the data as a stream of records in the response to be displayed in the browser window, but not the attributes. To access the attributes, use the "Extract Attributes (SingleTSFrame)" component.

**Note:** When wired to a generic REST adapter, the attributes are sent base64-encoded with the key "Data-Attributes" in the header. To process the attributes, the adapter should be implemented accordingly.
"""

import copy

from hdhelpers.metadata import attach_metadata, attrs_to_json

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
        "attributes": {"data_type": "ANY"},
    },
    "outputs": {
        "singletsframe": {"data_type": "SINGLETSFRAME"},
    },
    "name": "Add/Update Attributes (SingleTSFrame)",
    "category": "Connectors",
    "description": "Add attributes to a singletsframe or update attributes of a singletsframe",
    "version_tag": "1.0.0",
    "id": "feeea3fc-f676-4a77-b88d-0ed016fed11f",
    "revision_group_id": "ac47bf43-14e9-4832-bf6a-9c4a56f1b2a8",
    "state": "RELEASED",
    "released_timestamp": "2026-08-05T10:00:00+00:00",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(*, singletsframe, attributes):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.
    # a copy, since the input may also be used elsewhere in the workflow
    updated_singletsframe = singletsframe.copy()
    # attached metadata in its JSON form, so that it is updated, and attached again
    updated_singletsframe.attrs = copy.deepcopy(attrs_to_json(singletsframe.attrs))
    updated_singletsframe.attrs.update(copy.deepcopy(attributes))
    attach_metadata(updated_singletsframe, "SINGLETSFRAME")

    return {"singletsframe": updated_singletsframe}


# Testing
try:
    import pandas as pd
    import pytest
except ImportError:
    pass
else:
    from hdhelpers.metadata import META_KEY, read_metadata

    SINGLETSFRAME_METADATA = {
        "dataset_metadata": {
            "metric_key": "id",
            "single_metric": "abc.temp",
            "queried_metrics": ["abc.temp"],
            "ref_interval_start_timestamp": "2019-08-01T15:00:00Z",
            "ref_interval_end_timestamp": "2019-08-01T16:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": "abc.temp",
                "name": "Temperature",
                "value_dimensions": [{"column": "value", "unit": "°C", "measurement": None}],
            }
        ],
    }

    @pytest.fixture
    def singletsframe():
        singletsframe = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(["2019-08-01T15:42:36.000Z"], utc=True),
                "value": [1.0],
            }
        )
        singletsframe.attrs = {"dataset_metadata": {"single_metric": "abc.temp"}, "a": 1}
        return singletsframe

    def test_adds_and_updates_attributes(singletsframe):
        attributes = {"a": 2, "metrics": [{"id": "abc.temp", "name": "Temperature"}]}

        result = main(singletsframe=singletsframe, attributes=attributes)["singletsframe"]

        assert result.attrs == {  # noqa: S101
            "dataset_metadata": {"single_metric": "abc.temp"},
            "a": 2,
            "metrics": [{"id": "abc.temp", "name": "Temperature"}],
        }
        assert list(result["value"]) == [1.0]  # noqa: S101

    def test_updated_metadata_is_attached_again(singletsframe):
        singletsframe.attrs = copy.deepcopy(SINGLETSFRAME_METADATA)
        original = read_metadata(singletsframe, "SINGLETSFRAME", required=True)
        assert attach_metadata(singletsframe) is not None  # noqa: S101
        metrics = copy.deepcopy(SINGLETSFRAME_METADATA["metrics"])
        metrics[0]["value_dimensions"][0]["unit"] = "K"

        result = main(singletsframe=singletsframe, attributes={"metrics": metrics, "a": 1})[
            "singletsframe"
        ]

        assert set(result.attrs) == {META_KEY, "a"}  # noqa: S101
        assert read_metadata(result, "SINGLETSFRAME", required=True).unit() == "K"  # noqa: S101
        # the input keeps its metadata
        assert read_metadata(singletsframe, "SINGLETSFRAME") == original  # noqa: S101

    def test_metadata_not_following_conventions_after_the_update_is_not_attached(singletsframe):
        singletsframe.attrs = copy.deepcopy(SINGLETSFRAME_METADATA)
        attach_metadata(singletsframe)
        # e.g. the invalidation instructions for writing to the sql adapter
        attributes = {"dataset_metadata": {"invalidate_dataset": True}}

        result = main(singletsframe=singletsframe, attributes=attributes)["singletsframe"]

        assert result.attrs == {  # noqa: S101
            "dataset_metadata": {"invalidate_dataset": True},
            "metrics": SINGLETSFRAME_METADATA["metrics"],
        }

    def test_input_is_not_changed(singletsframe):
        attributes = {"a": 2, "metrics": [{"id": "abc.temp"}]}

        result = main(singletsframe=singletsframe, attributes=attributes)["singletsframe"]
        result.attrs["dataset_metadata"]["metric_key"] = "id"
        result.attrs["metrics"][0]["name"] = "Temperature"

        assert singletsframe.attrs == {  # noqa: S101
            "dataset_metadata": {"single_metric": "abc.temp"},
            "a": 1,
        }
        assert attributes == {"a": 2, "metrics": [{"id": "abc.temp"}]}  # noqa: S101


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [
        {
            "workflow_input_name": "singletsframe",
            "filters": {
                "value": '{\n    "value": [\n        1,\n        1.2,\n        0.5\n    ],\n    "timestamp": [\n        "2019-08-01T15:42:36.000Z",\n        "2019-08-01T15:45:36.000Z",\n        "2019-08-01T15:48:36.000Z"\n    ]\n}'
            },
        },
        {
            "workflow_input_name": "attributes",
            "filters": {"value": '{\n    "a": true,\n    "b": 31.56\n}'},
        },
    ]
}
RELEASE_WIRING = {}
