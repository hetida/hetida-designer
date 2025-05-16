from hdhelpers.plot_target_settings import plotly_fig_to_json_dict


def test_plotly_fig_to_json_dict():
    # TODO: Split into proper tests
    json_dict = plotly_fig_to_json_dict()
    assert isinstance(json_dict, dict)

