import pytest

from hetdesrun.trafoutils.io.load import load_trafos_from_trafo_list_json_file


@pytest.fixture
def all_base_trafos_from_file():
    loaded_trafos = load_trafos_from_trafo_list_json_file(
        "./tests/data/import_sources_examples/all_base_trafos_from_transformations_get_endpoint.json"
    )

    return loaded_trafos
