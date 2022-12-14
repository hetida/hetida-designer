from hetdesrun.trafoutils.io.load import load_trafos_from_trafo_list_json_file


def test_load_multiple_trafos_from_json_file():

    loaded_trafos = load_trafos_from_trafo_list_json_file(
        "./tests/data/all_base_trafos_from_transformations_get_endpoint.json"
    )

    assert len(loaded_trafos) > 10
