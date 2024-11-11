"""Documentation for Test Component Code Repr

Some documentation
"""

import io

import pandas as pd

# ***** DO NOT EDIT LINES BELOW *****
# These lines may be overwritten if component details or inputs/outputs change.
COMPONENT_INFO = {
    "inputs": {
        "x": {"data_type": "FLOAT", "default_value": 1.2},
        "ok": {"data_type": "BOOLEAN", "default_value": False},
        "neither_nor_ok": {"data_type": "BOOLEAN", "default_value": None},
        "text": {"data_type": "STRING", "default_value": "text"},
        "null_text": {"data_type": "STRING", "default_value": "null"},
        "empty_text": {"data_type": "STRING", "default_value": ""},
        "null_any": {"data_type": "ANY", "default_value": None},
        "empty_string_any": {"data_type": "ANY", "default_value": ""},
        "some_string_any": {"data_type": "ANY", "default_value": "text"},
        "some_number_any": {"data_type": "ANY", "default_value": 23},
        "some_json_any": {
            "data_type": "ANY",
            "default_value": {
                "test": True,
                "content": None,
                "sub_structure": {"relevant": False},
            },
        },
        "series": {
            "data_type": "SERIES",
            "default_value": {
                "2020-01-01T01:15:27.000Z": 42.2,
                "2020-01-03T08:20:03.000Z": 18.7,
                "2020-01-03T08:20:04.000Z": 25.9,
            },
        },
        "multitsframe": {
            "data_type": "MULTITSFRAME",
            "default_value": {
                "__hd_wrapped_data_object__": "DATAFRAME",
                "__metadata__": {"test": 43},
                "__data__": {
                    "metric": ["a", "b"],
                    "timestamp": [
                        "2023-01-01T00:00:00.000Z",
                        "2023-01-01T00:00:00.000Z",
                    ],
                    "value": [2.3, "t"],
                },
            },
        },
    },
    "outputs": {
        "x": {"data_type": "FLOAT"},
        "ok": {"data_type": "BOOLEAN"},
        "neither_nor_ok": {"data_type": "BOOLEAN"},
        "text": {"data_type": "STRING"},
        "null_text": {"data_type": "STRING"},
        "empty_text": {"data_type": "STRING"},
        "null_any": {"data_type": "ANY"},
        "empty_string_any": {"data_type": "ANY"},
        "some_string_any": {"data_type": "ANY"},
        "some_number_any": {"data_type": "ANY"},
        "some_json_any": {"data_type": "ANY"},
        "series": {"data_type": "SERIES"},
        "multitsframe": {"data_type": "MULTITSFRAME"},
    },
    "name": "Test Component Code Repr",
    "category": "Test",
    "description": "Just outputs its input value",
    "version_tag": "1.0.0",
    "id": "31cb6a1a-d409-4bb7-87a7-ee3d97940dfc",
    "revision_group_id": "d414eb7d-3954-4c96-a329-fd0cefe0613a",
    "state": "DRAFT",
}

from hdutils import parse_default_value  # noqa: E402, F401


def main(
    *,
    x=1.2,
    ok=False,
    neither_nor_ok=None,
    text="text",
    null_text="null",
    empty_text="",
    null_any=parse_default_value(COMPONENT_INFO, "null_any"),
    empty_string_any=parse_default_value(COMPONENT_INFO, "empty_string_any"),
    some_string_any=parse_default_value(COMPONENT_INFO, "some_string_any"),
    some_number_any=parse_default_value(COMPONENT_INFO, "some_number_any"),
    some_json_any=parse_default_value(COMPONENT_INFO, "some_json_any"),
    series=parse_default_value(COMPONENT_INFO, "series"),
    multitsframe=parse_default_value(COMPONENT_INFO, "multitsframe"),
):
    # entrypoint function for this component
    # ***** DO NOT EDIT LINES ABOVE *****
    # write your function code here.

    return {
        "x": x,
        "ok": ok,
        "neither_nor_ok": neither_nor_ok,
        "text": text,
        "null_text": null_text,
        "empty_text": empty_text,
        "null_any": null_any,
        "empty_string_any": empty_string_any,
        "some_string_any": some_string_any,
        "some_number_any": some_number_any,
        "some_json_any": some_json_any,
        "series": series,
        "multitsframe": multitsframe,
    }


TEST_WIRING_FROM_PY_FILE_IMPORT = {
    "input_wirings": [{"workflow_input_name": "x", "filters": {"value": "45.6"}}]
}
RELEASE_WIRING = None
