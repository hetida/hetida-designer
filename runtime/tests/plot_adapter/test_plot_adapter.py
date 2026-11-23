import json
import os
from typing import Any
from uuid import UUID

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from hdutils import DataType, plotly_fig_to_json_dict, serialize_dataframe
from hetdesrun.adapters.plot_adapter.default_plots import (
    provide_plotly_fig_json_for_arbitrary_value,
)
from hetdesrun.trafoutils.trafo_collection import TrafoCollection

payload = {
    "id": "bfa27afc-dea8-b8aa-4b15-94402f0739b6",
    "run_pure_plot_operators": True,
    "wiring": {
        "dashboard_positionings": [],
        "input_wirings": [
            {
                "adapter_id": "direct_provisioning",
                "filters": {
                    "value": '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}'  # noqa: E501
                },
                "use_default_value": False,
                "workflow_input_name": "input",
            }
        ],
        "output_wirings": [{"adapter_id": "plot", "filters": {}, "workflow_output_name": "output"}],
    },
}


def pt_payload(id: UUID, value_str: str, run_pure_plot_operators: bool = True) -> Any:  # noqa: A002
    payload = {
        "id": str(id),
        "run_pure_plot_operators": run_pure_plot_operators,
        "wiring": {
            "dashboard_positionings": [],
            "input_wirings": [
                {
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": value_str},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [
                {"adapter_id": "plot", "filters": {}, "workflow_output_name": "output"}
            ],
        },
    }
    return payload


def assert_resp_has_plot_output(resp):
    assert resp.status_code == 200
    resp_json = resp.json()
    assert resp_json["error"] is None

    # output type was appropriately adapted:
    assert resp_json["output_types_by_output_name"]["output"] == "PLOTLYJSON"

    # result is a plotly json dict object
    plot_result = resp_json["output_results_by_output_name"]["output"]
    assert isinstance(plot_result, dict)
    assert "data" in plot_result


@pytest.mark.asyncio
async def test_plot_wiring_payload(mocked_clean_test_db_session, async_test_client):
    with TrafoCollection(save_to_db=True) as tc:
        pt_series = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
            )
        )
        pt_dataframe = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-dataframe_100_7a1a818f-fa89-6062-1e0e-fc80539bbe0a.json",
            )
        )
        pt_mtfs = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-multitsframe_100_78ee6b00-9239-4214-b9bf-a093647f33f5.json",
            )
        )
        pt_string = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
            )
        )

        pt_any = tc.add_from_json_file(
            os.path.join(
                "transformations",
                "components",
                "connectors",
                "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json",
            )
        )

    async with async_test_client as client:
        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_series.id,
                '{\n    "2020-01-01T01:15:27.000Z": 42.2,\n    "2020-01-03T08:20:03.000Z": 18.7,\n    "2020-01-03T08:20:04.000Z": 25.9\n}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_string.id,
                "some string",  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_dataframe.id,
                '{    "column1": {        "2019-08-01T15:45:36.000Z": 1,        "2019-08-02T11:33:41.000Z": 2    },    "column2": {        "2019-08-01T15:45:36.000Z": 1.3,        "2019-08-02T11:33:41.000Z": 2.8    }}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_mtfs.id,
                '{    "value": [        1,        1.2,        0.5    ],    "metric": [        "a",        "b",        "c"    ],    "timestamp": [        "2019-08-01T15:45:36.000Z",        "2019-08-01T15:48:36.000Z",        "2019-08-01T15:42:36.000Z"    ]}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_any.id,
                '{"a": 42}',  # noqa: E501
            ),
        )

        assert_resp_has_plot_output(resp)
        assert plot_title_text(resp.json()["output_results_by_output_name"]["output"]) == (
            "<b>Unplottable ANY object</b>"
        )

        # Pandas objects on an ANY output, provided in the wrapped format via the ANY input
        for wrapped_data_object, data, expected_traces in [
            (
                "SERIES",
                {"2020-01-01T01:15:27.000Z": 42.2, "2020-01-03T08:20:03.000Z": 18.7},
                [("scatter", None)],
            ),
            (
                "DATAFRAME",
                {"column1": [1, 2], "column2": ["x", "y"]},
                [("table", None)],
            ),
            (
                "DATAFRAME",
                {
                    "timestamp": ["2019-08-01T15:45:36.000Z", "2019-08-01T15:48:36.000Z"],
                    "metric": ["a", "b"],
                    "value": [1, 1.2],
                },
                [("scatter", "a"), ("scatter", "b")],
            ),
        ]:
            resp = await client.post(
                "/api/transformations/execute",
                json=pt_payload(
                    pt_any.id,
                    json.dumps(
                        {
                            "__hd_wrapped_data_object__": wrapped_data_object,
                            "__metadata__": {},
                            "__data__": data,
                        }
                    ),
                ),
            )

            assert_resp_has_plot_output(resp)
            plot_result = resp.json()["output_results_by_output_name"]["output"]
            assert [
                (trace["type"], trace.get("name")) for trace in plot_result["data"]
            ] == expected_traces

        # Test setting run_pure_plot_adapters to false

        resp = await client.post(
            "/api/transformations/execute",
            json=pt_payload(
                pt_mtfs.id,
                '{    "value": [        1,        1.2,        0.5    ],    "metric": [        "a",        "b",        "c"    ],    "timestamp": [        "2019-08-01T15:45:36.000Z",        "2019-08-01T15:48:36.000Z",        "2019-08-01T15:42:36.000Z"    ]}',  # noqa: E501
                run_pure_plot_operators=False,
            ),
        )
        assert resp.status_code == 200
        resp_json = resp.json()
        assert resp_json["error"] is None

        # output type was appropriately adapted:
        assert resp_json["output_types_by_output_name"]["output"] == "PLOTLYJSON"

        # result is a plotly json dict object
        plot_result = resp_json["output_results_by_output_name"]["output"]
        assert isinstance(plot_result, dict)
        assert len(plot_result) == 0  # empty dict


def test_default_plot_for_singletsframe_uses_value_dimensions_as_traces():
    """A SingleTSFrame gets one trace / y axis per value dimension, not per metric"""
    singletsframe = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"], utc=True),
            "value": [1.0, 1.2],
            "score": [0.7, 0.2],
        }
    )

    plotly_json = provide_plotly_fig_json_for_arbitrary_value(singletsframe, DataType.SingleTSFrame)

    assert len(plotly_json["data"]) == 2
    assert {trace["name"] for trace in plotly_json["data"]} == {"value", "score"}
    # each value dimension gets its own y axis
    assert {trace["yaxis"] for trace in plotly_json["data"]} == {"y", "y2"}


def plot_title_text(plotly_json: Any) -> str:
    """Text of a plot showing a single value, see value_fig"""
    return plotly_json["data"][0]["title"]["text"]


MULTITSFRAME = pd.DataFrame(
    {
        "timestamp": pd.to_datetime(
            ["2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"], utc=True
        ),
        "metric": ["a", "b", "a"],
        "value": [1.0, 2.0, 1.5],
    }
)

# wide format timeseries data
WIDE_TIMESERIES_FRAME = pd.DataFrame(
    {
        "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"], utc=True),
        "a": [1.0, 1.5],
        "b": [2.0, None],
    }
)


@pytest.mark.parametrize(
    ("value", "data_type"),
    [
        (
            pd.Series([1.0, 2.0], index=pd.to_datetime(["2020-01-01", "2020-01-02"], utc=True)),
            "SERIES",
        ),
        (pd.Series([1.0, 2.0]), "SERIES"),
        (MULTITSFRAME, "MULTITSFRAME"),
        # additional columns, e.g. from metadata
        (MULTITSFRAME.assign(unit="m"), "MULTITSFRAME"),
        # wide format timeseries data: line plot
        (WIDE_TIMESERIES_FRAME, "DATAFRAME"),
        # no datetimes in the timestamp column, so no MultiTSFrame: table
        (MULTITSFRAME.astype({"timestamp": str}), "DATAFRAME"),
        # metrics which cannot be plotted as trace names: table
        (MULTITSFRAME.assign(metric=[("a", 1), ("b", 1), ("a", 1)]), "DATAFRAME"),
        (pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}), "DATAFRAME"),
        (pd.DataFrame(), "DATAFRAME"),
    ],
)
def test_default_plot_for_pandas_object_on_any_output_is_chosen_by_its_structure(value, data_type):
    assert provide_plotly_fig_json_for_arbitrary_value(
        value, DataType.Any
    ) == provide_plotly_fig_json_for_arbitrary_value(value, DataType(data_type))


def test_default_plot_for_dataframe_with_timestamp_column_is_a_line_plot():
    df = WIDE_TIMESERIES_FRAME

    for data_type in (DataType.DataFrame, DataType.Any):
        plotly_json = provide_plotly_fig_json_for_arbitrary_value(df, data_type)
        assert {trace["type"] for trace in plotly_json["data"]} == {"scatter"}
        assert {trace["name"] for trace in plotly_json["data"]} == {"a", "b"}

    # table, if not possible
    df_mixed_types = df.assign(b=["x", "y"])
    for data_type in (DataType.DataFrame, DataType.Any):
        plotly_json = provide_plotly_fig_json_for_arbitrary_value(df_mixed_types, data_type)
        assert [trace["type"] for trace in plotly_json["data"]] == ["table"]


@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("some string", "some string"),
        (42, "42"),
        (4.2, "4.2"),
        (True, "True"),
        (np.int64(42), "42"),
        (np.float64(4.2), "4.2"),
        (np.bool_(False), "False"),
        (None, "None"),
        (pd.Timestamp("2020-01-01T00:00:00Z"), "2020-01-01 00:00:00+00:00"),
        ({"a": 42}, "Unplottable ANY object"),
        ([1, 2], "Unplottable ANY object"),
        (np.array([1, 2]), "Unplottable ANY object"),
        # wrapped format of a DataFrame, which components may output via ANY outputs
        (serialize_dataframe(MULTITSFRAME), "Unplottable ANY object"),
    ],
)
def test_default_plot_for_other_values_on_any_output_shows_value_or_unplottable(value, text):
    assert plot_title_text(provide_plotly_fig_json_for_arbitrary_value(value, DataType.Any)) == (
        f"<b>{text}</b>"
    )


def test_default_plot_for_plotly_figure_or_plotly_json_on_any_output_is_the_plot_itself():
    fig = go.Figure(go.Bar(x=["a", "b"], y=[1, 2]))
    fig_dict_before = fig.to_dict()

    plotly_json = provide_plotly_fig_json_for_arbitrary_value(fig, DataType.Any)

    assert plotly_json == plotly_fig_to_json_dict(go.Figure(fig))
    assert fig.to_dict() == fig_dict_before  # figure is not changed

    # e.g. the output of a visualization component passed through an ANY output
    assert provide_plotly_fig_json_for_arbitrary_value(plotly_json, DataType.Any) is plotly_json
    assert provide_plotly_fig_json_for_arbitrary_value(
        {"data": [], "layout": {}}, DataType.Any
    ) == {
        "data": [],
        "layout": {},
    }
    # not plotly json
    for value in ({"data": [1, 2]}, {"data": [], "layout": {}, "other": 1}, {"data": {}}):
        assert plot_title_text(
            provide_plotly_fig_json_for_arbitrary_value(value, DataType.Any)
        ) == ("<b>Unplottable ANY object</b>")
