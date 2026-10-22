"""Base components working on MULTITSFRAMEs without their metadata

pandas copies the metadata (attrs) of a DataFrame on every operation, which is costly for the
metadata of many metrics in loops over the metrics. Hence such components work on the data
without its metadata. These tests ensure that this neither changes their results nor their
inputs.
"""

import copy
import json

import pandas as pd
import pytest

from hetdesrun.component.load import import_func_from_code_wrapper

COMPONENTS_PATH = "transformations/components/"


def component_main(path: str):  # type: ignore[no-untyped-def]
    with open(COMPONENTS_PATH + path) as f:
        code = json.load(f)["content"]
    return import_func_from_code_wrapper(code, "main")


def multitsframe_with_metadata() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-10-18T06:00:00Z",
                    "2026-10-18T06:00:00Z",
                    "2026-10-18T07:00:00Z",
                    "2026-10-18T07:00:00Z",
                ],
                utc=True,
            ),
            "metric": pd.Series(["a", "b", "a", "b"], dtype="string"),
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )
    frame.attrs = {
        "dataset_metadata": {
            "metric_key": "id",
            "queried_metrics": ["a", "b"],
            "ref_interval_start_timestamp": "2026-10-18T00:00:00Z",
            "ref_interval_end_timestamp": "2026-10-19T00:00:00Z",
            "ref_interval_type": "closed",
        },
        "metrics": [
            {
                "id": metric,
                "name": f"Metric {metric}",
                "comments": [{"content": "maintenance", "tags": ["maintenance"]}],
                "inherited": {"latitude": 51.43},
                "value_dimensions": [{"column": "value", "unit": "m", "measurement": "level"}],
            }
            for metric in ("a", "b")
        ],
    }
    return frame


@pytest.mark.parametrize(
    "path",
    [
        "visualization/multitsframe-plot-with-multiple-y-axes_100_28120522-a6a5-418f-a658-ab19d5beefe2.json",
        "connectors/convert-multitsframe-to-dataframe_100_ed88477a-72f5-475b-b3e6-9b0e030609b6.json",
    ],
)
def test_result_and_input_are_unaffected(path: str) -> None:
    main = component_main(path)
    multitsframe = multitsframe_with_metadata()
    expected_input = multitsframe.copy()
    expected_attrs = copy.deepcopy(multitsframe.attrs)
    without_metadata = multitsframe.copy()
    without_metadata.attrs = {}

    result = main(multitsframe=multitsframe)  # type: ignore[operator]
    result_without_metadata = main(multitsframe=without_metadata)  # type: ignore[operator]

    assert result.keys() == result_without_metadata.keys()
    for name, output in result.items():
        if isinstance(output, pd.DataFrame):
            pd.testing.assert_frame_equal(output, result_without_metadata[name])
            # as before: pandas does not pass the metadata on to the constructed output
            assert output.attrs == {}
        else:
            assert output == result_without_metadata[name]
    assert multitsframe.attrs == expected_attrs
    pd.testing.assert_frame_equal(multitsframe, expected_input)
