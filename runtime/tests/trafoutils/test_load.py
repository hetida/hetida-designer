from hetdesrun.trafoutils.io.load import (
    get_import_sources,
    load_trafos_from_trafo_list_json_file,
)


def test_load_multiple_trafos_from_json_file():

    loaded_trafos = load_trafos_from_trafo_list_json_file(
        "./tests/data/import_sources_examples/all_base_trafos_from_transformations_get_endpoint.json"
    )

    assert len(loaded_trafos) > 10


def test_get_import_sources():
    import_sources = list(get_import_sources("./tests/data/import_sources_directory"))
    assert len(import_sources) == 4

    assert (
        len([imp_src for imp_src in import_sources if imp_src.config_file is not None])
        == 2
    )

    assert len([imp_src for imp_src in import_sources if imp_src.is_dir]) == 2
