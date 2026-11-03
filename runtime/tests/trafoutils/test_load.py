from hetdesrun.trafoutils.io.load import (
    TrafoList,
    get_import_sources,
    load_import_sources_from_directory,
    load_trafos_from_json_file,
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

    assert len([imp_src for imp_src in import_sources if imp_src.config_file is not None]) == 2

    assert len([imp_src for imp_src in import_sources if imp_src.is_dir]) == 2


def test_load_import_sources_from_directory():
    importables = load_import_sources_from_directory("./tests/data/import_sources_examples")
    assert len(importables) == 2

    assert (
        len(
            [
                imp
                for imp in importables
                if imp.import_config.filter_params.category_prefix is not None
            ]
        )
        == 1
    )


def test_get_import_sources_with_python_files(tmp_path):
    (tmp_path / "subdir").mkdir()
    for name in ("b.json", "a.py", "a.py.config.json", "__init__.py", "notes.txt"):
        (tmp_path / name).write_text("")

    import_sources = list(get_import_sources(str(tmp_path)))

    assert [(src.path, src.is_dir, src.config_file) for src in import_sources] == [
        (str(tmp_path / "a.py"), False, str(tmp_path / "a.py.config.json")),
        (str(tmp_path / "b.json"), False, None),
        (str(tmp_path / "subdir"), True, None),
    ]


def test_load_trafos_from_json_file(tmp_path):
    trafos = load_trafos_from_trafo_list_json_file(
        "./tests/data/import_sources_examples/all_base_trafos_from_transformations_get_endpoint.json"
    )
    (tmp_path / "list.json").write_text(TrafoList(trafos[:2]).model_dump_json())
    (tmp_path / "single.json").write_text(trafos[2].model_dump_json())

    assert load_trafos_from_json_file(str(tmp_path / "list.json")) == trafos[:2]
    assert load_trafos_from_json_file(str(tmp_path / "single.json")) == [trafos[2]]


def test_get_import_sources_of_kubernetes_configmap(tmp_path):
    """A configmap mounted as directory contains its files via hidden entries"""
    data_dir = tmp_path / "..2026_10_29_12_00_00.123"
    data_dir.mkdir()
    (data_dir / "my_trafos.json").write_text("[]")
    (data_dir / "my_trafos.json.config.json").write_text("{}")
    (tmp_path / "..data").symlink_to(data_dir.name)
    (tmp_path / "my_trafos.json").symlink_to("..data/my_trafos.json")
    (tmp_path / "my_trafos.json.config.json").symlink_to("..data/my_trafos.json.config.json")

    import_sources = list(get_import_sources(str(tmp_path)))

    assert [(src.path, src.is_dir, src.config_file) for src in import_sources] == [
        (str(tmp_path / "my_trafos.json"), False, str(tmp_path / "my_trafos.json.config.json"))
    ]
