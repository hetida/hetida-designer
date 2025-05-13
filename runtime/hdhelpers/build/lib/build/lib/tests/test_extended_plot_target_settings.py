import pandas as pd
import pytest

from hdhelpers.hdhelpers.extended_plot_target_settings import (
    _get_display_name,
    _get_unit,
    get_colors,
    get_period,
    modify_timezone,
    set_layout,
    set_traces,
    set_xaxes,
    set_yaxes,
)


def test_get_colors():
    colors = get_colors()
    assert bool(colors) is True
    assert "grid_color" in colors


@pytest.mark.parametrize(
    ("legend_position", "margins", "show_grid", "template", "show_zero_line", "expected_result"),
    [
        (
            None,
            None,
            True,
            "simple_white",
            True,
            {
                "margin": {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
                "legend": {},
                "template": "simple_white",
                "plot_bgcolor": get_colors()["background_color"],
                "xaxis": {
                    "showgrid": True,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": True,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "yaxis": {
                    "showgrid": True,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": True,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "autosize": True,
                "showlegend": False,
            },
        ),
        (
            "default",
            None,
            True,
            "simple_white",
            True,
            {
                "margin": {"autoexpand": True, "l": 0, "r": 0, "b": 0, "t": 0, "pad": 0},
                "legend": {},
                "template": "simple_white",
                "plot_bgcolor": get_colors()["background_color"],
                "xaxis": {
                    "showgrid": True,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": True,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "yaxis": {
                    "showgrid": True,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": True,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "autosize": True,
                "showlegend": True,
            },
        ),
        (
            {
                "orientation": "v",
                "yanchor": "top",
                "y": 1.0,
                "xanchor": "left",
                "x": 0.0,
                "bgcolor": "rgba(240,240,240,0.5)",
            },
            {"autoexpand": False, "l": 10, "r": 10, "b": 50, "t": 20, "pad": 0},
            False,
            "seaborn",
            False,
            {
                "margin": {"autoexpand": False, "l": 10, "r": 10, "b": 50, "t": 20, "pad": 0},
                "legend": {
                    "orientation": "v",
                    "yanchor": "top",
                    "y": 1.0,
                    "xanchor": "left",
                    "x": 0.0,
                    "bgcolor": "rgba(240,240,240,0.5)",
                },
                "template": "seaborn",
                "plot_bgcolor": get_colors()["background_color"],
                "xaxis": {
                    "showgrid": False,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": False,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "yaxis": {
                    "showgrid": False,
                    "gridcolor": get_colors()["grid_color"],
                    "zeroline": False,
                    "zerolinecolor": get_colors()["grid_color"],
                },
                "autosize": True,
                "showlegend": True,
            },
        ),
    ],
)
def test_set_layout(
    legend_position: dict | str | None,
    margins: dict | None,
    show_grid: bool,
    template: str,
    show_zero_line: bool,
    expected_result: dict,
):
    layout = set_layout(
        legend_position=legend_position,
        margins=margins,
        show_grid=show_grid,
        template=template,
        zero_line=show_zero_line,
    )
    assert layout == expected_result


@pytest.mark.parametrize(
    ("default_title", "attrs", "expected_result"),
    [
        ("", {}, ""),
        ("foo", {}, "foo"),
        (
            "bar",
            {
                "single_metric_metadata": {
                    "structured_metadata": {"metric": {"short_display_name": "bar"}}
                }
            },
            "bar",
        ),
    ],
)
def test_get_display_name(default_title, attrs, expected_result):
    series = pd.Series()
    series.attrs = attrs
    title = _get_display_name(series, default_title)
    assert title == expected_result


@pytest.mark.parametrize(
    ("default_unit", "attrs", "expected_result"),
    [
        ("", {}, ""),
        ("foo", {}, "foo"),
        (
            "bar",
            {"single_metric_metadata": {"structured_metadata": {"metric": {"unit": "bar"}}}},
            "bar",
        ),
    ],
)
def test_get_unit(default_unit, attrs, expected_result):
    series = pd.Series()
    series.attrs = attrs
    unit = _get_unit(series, default_unit)
    assert unit == expected_result


@pytest.mark.parametrize(
    ("attrs", "standoff", "default_title", "default_unit", "expected_result"),
    [
        (
            {},
            5,
            "",
            "",
            {
                "automargin": True,
                "title_standoff": 5,
                "title_text": "",
            },
        ),
        (
            {},
            5,
            "foo",
            "bar",
            {
                "automargin": True,
                "title_standoff": 5,
                "title_text": "foo [bar]",
            },
        ),
        (
            {
                "single_metric_metadata": {
                    "structured_metadata": {"metric": {"short_display_name": "bar", "unit": "baz"}}
                }
            },
            15,
            "foo",
            "bar",
            {
                "automargin": True,
                "title_standoff": 15,
                "title_text": "bar [baz]",
            },
        ),
    ],
)
def test_set_yaxes(
    attrs: dict, standoff: int, default_title: str, default_unit: str, expected_result: dict
):
    series = pd.Series()
    series.attrs = attrs
    yaxes = set_yaxes(series, standoff, default_title, default_unit)
    assert yaxes == expected_result


def test_get_period():
    # TODO: When the concept is done @Confluence
    start, end = get_period(pd.Series(), "Europe/Berlin")
    assert isinstance(start, pd.Timestamp)
    assert isinstance(end, pd.Timestamp)
    assert end >= start


def test_set_xaxes():
    # TODO: When test_get_period is done
    xaxes = set_xaxes(pd.Series())
    assert isinstance(xaxes, dict)


@pytest.mark.parametrize(
    ("line_width", "marker_mode", "marker_size", "marker_symbol", "expected_result"),
    [
        (
            1,
            "lines+markers",
            3,
            "circle",
            {
                "marker": {"size": 3},
                "line": {"width": 1},
                "mode": "lines+markers",
                "marker_symbol": "circle",
            },
        ),
        (
            3,
            "markers",
            2,
            "x-thin",
            {
                "marker": {"size": 2},
                "line": {"width": 3},
                "mode": "markers",
                "marker_symbol": "x-thin",
            },
        ),
    ],
)
def test_set_traces(
    line_width: int, marker_mode: str, marker_size: int, marker_symbol: str, expected_result: dict
):
    traces = set_traces(line_width, marker_mode, marker_size, marker_symbol)
    assert traces == expected_result


def test_modify_timezone():
    # TODO: modify_timezone is the last function to be overhauled; this is a placeholder
    converted_object = modify_timezone()
    assert converted_object is None
