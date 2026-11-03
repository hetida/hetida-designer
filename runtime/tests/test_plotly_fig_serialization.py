"""serialize_plotly_fig must give the same result as json.loads(fig.to_json())

serialize_plotly_fig reimplements parts of fig.to_json() to be faster, see its docstring.
These tests compare both ways for figures which run through all steps of fig.to_json(),
so that they fail if a Plotly version handles any of them differently.
"""

import base64
import datetime
import decimal
import json
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from PIL import Image
from plotly.utils import PlotlyJSONEncoder

from hdutils import serialize_plotly_fig


def serialize_via_to_json(fig: go.Figure) -> Any:
    """The way serialize_plotly_fig worked before, as reference

    engine="json" since this is what was used: The default engine "auto" uses the json
    module as long as orjson is not installed.
    """
    return json.loads(fig.to_json(validate=False, engine="json"))


def empty_fig() -> go.Figure:
    return go.Figure()


def timeseries_fig() -> go.Figure:
    index = pd.date_range("2024-01-01", periods=1000, freq="1234567us")
    values = np.random.default_rng(0).standard_normal(len(index))
    return go.Figure(go.Scatter(x=index, y=values))


def timezone_aware_fig() -> go.Figure:
    # covers the change from daylight saving time, when 02:00 to 03:00 occurs twice
    index = pd.date_range("2024-10-27 00:00", periods=6, freq="h", tz="Europe/Berlin")
    series = pd.Series(np.arange(6.0), index=index)
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=series)
    fig.add_scatter(x=series.index.to_series(), y=series)
    fig.add_scatter(x=list(index.to_pydatetime()), y=series.to_list())
    fig.update_xaxes(range=[index[0], index[-1]])
    return fig


def nan_and_infinity_fig() -> go.Figure:
    fig = go.Figure()
    fig.add_scatter(x=[1, 2, 3, 4], y=[1.0, float("nan"), float("inf"), float("-inf")])
    fig.add_scatter(x=[1, 2, 3, 4], y=np.array([1.0, np.nan, np.inf, -np.inf]))
    fig.add_scatter(
        x=[pd.NaT, pd.Timestamp("2024-01-01"), None, np.datetime64("NaT", "ns")], y=[1, 2, 3, 4]
    )
    return fig


def nan_text_fig() -> go.Figure:
    # "NaN" and "Infinity" in texts make Plotly encode again, "<", ">" and "/" are escaped
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4], name="NaN", text=["Infinity", "<b>a/b</b>"]))
    fig.update_layout(title="Values: NaN / Infinity </script>")
    return fig


def base64_containing_nan_fig() -> go.Figure:
    # values whose base64 encoding contains "NaN", as it happens by chance for large plots
    values = np.frombuffer(base64.b64decode("NaNANaNA"), dtype="u1")
    return go.Figure(go.Bar(y=values))


def uid_fig() -> go.Figure:
    return go.Figure([go.Scatter(y=[1, 2], uid="first"), go.Bar(y=[3, 4], uid="second")])


def other_values_fig() -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=[
                decimal.Decimal("1.5"),
                datetime.date(2024, 1, 1),
                datetime.time(12, 30),
                np.int64(3),
                np.float32(0.5),
                np.bool_(True),
                np.datetime64("2024-01-01T00:00:00.123456789"),
                np.ma.masked,
            ],
            y=np.arange(8),
            customdata=np.arange(16).reshape(8, 2),
            text=np.array(list("abcdefgh")),
            selectedpoints=np.array([True, False] * 4),
        )
    )
    fig.add_layout_image(source=Image.new("RGB", (2, 2)), x=0, y=0)
    fig.frames = [go.Frame(data=[go.Scatter(y=[1, 2])], name="frame")]
    return fig


FIGURES: dict[str, Callable[[], go.Figure]] = {
    "empty": empty_fig,
    "timeseries": timeseries_fig,
    "timezone_aware": timezone_aware_fig,
    "nan_and_infinity": nan_and_infinity_fig,
    "nan_text": nan_text_fig,
    "base64_containing_nan": base64_containing_nan_fig,
    "uid": uid_fig,
    "other_values": other_values_fig,
}


@pytest.mark.parametrize("make_fig", FIGURES.values(), ids=FIGURES.keys())
def test_serialize_plotly_fig_agrees_with_to_json(make_fig: Callable[[], go.Figure]) -> None:
    fig = make_fig()
    expected = serialize_via_to_json(fig)

    result = serialize_plotly_fig(fig)

    assert result == expected
    # also the same order of keys and types of numbers, which == ignores (1 == 1.0 == True)
    assert json.dumps(result) == json.dumps(expected)


def test_figures_run_through_all_steps_of_to_json() -> None:
    """Make sure the figures above reach the steps of fig.to_json() reimplemented or skipped"""
    assert all("uid" in trace for trace in uid_fig().to_dict()["data"])

    for make_fig in [nan_and_infinity_fig, nan_text_fig, base64_containing_nan_fig]:
        encoded = json.dumps(make_fig().to_dict(), default=PlotlyJSONEncoder().default)
        assert "NaN" in encoded

    assert "\\u002f" in nan_text_fig().to_json(engine="json")


def test_serialize_plotly_fig_returns_dicts_unchanged() -> None:
    fig_dict = {"data": [{"type": "scatter", "y": [1, 2]}], "layout": {}}

    assert serialize_plotly_fig(fig_dict) is fig_dict
