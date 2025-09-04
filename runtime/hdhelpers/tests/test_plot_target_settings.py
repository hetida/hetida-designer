import plotly.graph_objects as go

from hdhelpers.plot_target_settings import plotly_fig_to_json_dict


def test_plotly_fig_to_json_dict_defaults():
    plotly_fig = go.Figure()
    plotly_fig.add_trace(
        go.Scatter(
            x=[1, 2, 3],
            y=[9, 8, 7],
            name="Foo",
        )
    )
    json_dict = plotly_fig_to_json_dict(plotly_fig)
    assert len(json_dict.get("layout", {}).get("template", {}).get("layout", {})["colorway"]) > 0
    assert json_dict.get("layout", {}).get("margin", {})["autoexpand"]
    assert json_dict.get("layout", {}).get("margin", {})["l"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["r"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["b"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["t"] == 0
    assert json_dict.get("layout", {}).get("margin", {})["pad"] == 0


def test_plotly_fig_to_json_dict_set_everything():
    plotly_fig = go.Figure()
    plotly_fig.add_trace(
        go.Scatter(
            x=[1, 2, 3],
            y=[9, 8, 7],
            name="Foo",
        )
    )
    json_dict = plotly_fig_to_json_dict(
        fig=plotly_fig,
        add_config_settings=False,
        hide_legend=True,
        hide_x_title=True,
        update_x_axes_tickformat=True,
        use_default_standoff=True,
        use_minimum_margin=False,
        use_muplot_axes_color=True,
        use_muplot_grid=True,
        use_muplot_line_and_markers=True,
        use_platform_background=True,
        use_platform_defaults=True,
        use_simple_white_template=False,
    )
    assert isinstance(json_dict, dict)

    assert len(json_dict.get("layout", {}).get("template", {}).get("layout", {})["colorway"]) > 0
    assert json_dict.get("layout", {}).get("margin", {}) == {}


# TODO: Negative Test for serialization?
