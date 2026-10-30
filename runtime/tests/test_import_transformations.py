import json
import logging
import os
import shutil
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
from uuid import UUID

import pytest

from hetdesrun.component.code import ParseDefaultValueError
from hetdesrun.datatypes import DataType
from hetdesrun.exportimport.importing import (
    autodeploy_base_transformations,
    autoimport_at_backend_start,
    autoimport_from_directory,
    generate_import_order_file,
    import_importable,
    import_importables,
    import_transformations_from_dir,
)
from hetdesrun.exportimport.utils import update_or_create_transformation_revision
from hetdesrun.persistence.dbservice.exceptions import DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
)
from hetdesrun.persistence.models.io import InputType
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import (
    get_import_sources,
    load_import_source,
    load_json,
    transformation_revision_from_python_code,
)


def test_tr_from_code_for_component_without_register_decorator():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.py",
    )
    with open(path) as f:
        code = f.read()

    tr = transformation_revision_from_python_code(code)

    assert tr.name == "Alerts from Score"
    assert tr.category == "Anomaly Detection"
    assert "anomalous situations" in tr.description
    assert tr.version_tag == "1.0.0"
    assert str(tr.id) == "38f168ef-cb06-d89c-79b3-0cd823f32e9d"
    assert str(tr.revision_group_id) == "38f168ef-cb06-d89c-79b3-0cd823f32e9d"
    assert len(tr.io_interface.inputs) == 2
    assert len(tr.io_interface.outputs) == 1
    assert tr.type == "COMPONENT"
    assert "COMPONENT_INFO" in tr.content
    assert "TEST_WIRING_FROM_PY_FILE_IMPORT" in tr.content
    assert len(tr.test_wiring.input_wirings) == 2


def test_tr_from_code_for_component_with_usual_optional_inputs():
    path = os.path.join(
        "tests",
        "data",
        "components",
        "univariate-linear-rul-regression_110_3fae802f-e4bf-424b-bf04-ec696e720281.py",
    )
    with open(path) as f:
        code = f.read()

    tr = transformation_revision_from_python_code(code)

    assert tr.name == "Univariate Linear RUL Regression"
    assert tr.category == "Remaining Useful Life"
    assert "on univariate timeseries" in tr.description
    assert tr.version_tag == "1.1.0 Copy"
    assert str(tr.id) == "e8ab3aa4-103c-4515-b690-8fd07e294711"
    assert str(tr.revision_group_id) == "6c73f83b-19f0-4caf-b97b-a25e21b93ed5"
    assert len(tr.io_interface.inputs) == 4
    assert tr.io_interface.inputs[0].name == "num_pred_series_future_days"
    assert tr.io_interface.inputs[0].data_type == DataType.Integer
    assert tr.io_interface.inputs[0].type == InputType.OPTIONAL
    assert tr.io_interface.inputs[0].value == "3"
    assert tr.io_interface.inputs[1].name == "pred_series_frequency"
    assert tr.io_interface.inputs[1].data_type == DataType.String
    assert tr.io_interface.inputs[1].type == InputType.OPTIONAL
    assert tr.io_interface.inputs[1].value == "5min"
    assert tr.io_interface.inputs[2].name == "timeseries"
    assert tr.io_interface.inputs[2].data_type == DataType.Series
    assert tr.io_interface.inputs[2].type == InputType.REQUIRED
    assert tr.io_interface.inputs[3].name == "limit"
    assert tr.io_interface.inputs[3].data_type == DataType.Float
    assert tr.io_interface.inputs[3].type == InputType.REQUIRED
    assert len(tr.io_interface.outputs) == 4
    assert tr.io_interface.outputs[0].name == "intercept"
    assert tr.io_interface.outputs[0].data_type == DataType.Float
    assert tr.io_interface.outputs[1].name == "slope"
    assert tr.io_interface.outputs[1].data_type == DataType.Float
    assert tr.io_interface.outputs[2].name == "pred_series"
    assert tr.io_interface.outputs[2].data_type == DataType.Series
    assert tr.io_interface.outputs[3].name == "limit_violation_prediction_timestamp"
    assert tr.io_interface.outputs[3].data_type == DataType.String
    assert tr.type == "COMPONENT"
    assert "COMPONENT_INFO" in tr.content


def test_tr_from_code_for_component_with_edge_case_optional_inputs():
    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_optional_inputs_component.py",
    )
    with open(py_path) as f:
        code = f.read()

    tr_from_py = transformation_revision_from_python_code(code)

    json_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_optional_inputs_component.json",
    )

    tr_from_json_json = load_json(json_path)
    tr_from_json = TransformationRevision(**tr_from_json_json)

    assert len(tr_from_py.io_interface.inputs) == len(tr_from_json.io_interface.inputs)
    nof_inputs = len(tr_from_py.io_interface.inputs)

    for input_index in range(nof_inputs):
        assert (
            tr_from_py.io_interface.inputs[input_index].name
            == tr_from_json.io_interface.inputs[input_index].name
        )
        assert (
            tr_from_py.io_interface.inputs[input_index].data_type
            == tr_from_json.io_interface.inputs[input_index].data_type
        )
        if input_index == 6:
            assert tr_from_py.io_interface.inputs[input_index].value is None
            assert tr_from_json.io_interface.inputs[input_index].value == "null"
            continue
        if input_index == 11:
            assert tr_from_py.io_interface.inputs[input_index].value == (
                tr_from_json.io_interface.inputs[input_index].value
            )
            continue
        assert (
            tr_from_py.io_interface.inputs[input_index].value
            == tr_from_json.io_interface.inputs[input_index].value
        )


def test_optional_input_default_value_parsing(mocked_clean_test_db_session):
    py_path = os.path.join(
        "tests",
        "data",
        "components",
        "test_optional_inputs_component_unparsable_default_values.py",
    )
    with open(py_path) as f:
        code = f.read()

    tr_from_py = transformation_revision_from_python_code(code)  # works
    with pytest.raises(ParseDefaultValueError):
        update_or_create_transformation_revision(tr_from_py, directly_in_db=True)


def test_import_single_transformation(mocked_clean_test_db_session):
    path = (
        "./transformations/components/arithmetic/"
        "consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json"
    )
    tr_json = load_json(path)
    tr = TransformationRevision(**tr_json)
    update_or_create_transformation_revision(tr, directly_in_db=True)
    persisted_tr = read_single_transformation_revision(tr.id)

    assert persisted_tr == tr


def test_component_import_via_rest_api(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200
    response_mock.json = mock.Mock(return_value={})

    with caplog.at_level(logging.DEBUG):  # noqa: SIM117
        with mock.patch("hetdesrun.utils.requests.put", return_value=response_mock) as patched_put:
            caplog.clear()
            import_transformations_from_dir("./transformations/components")

    # 1 call to multiple put endpoint
    assert patched_put.call_count == 1


def test_workflow_import_via_rest_api(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200
    response_mock.json = mock.Mock(return_value={})

    with mock.patch("hetdesrun.utils.requests.put", return_value=response_mock) as patched_put:
        import_transformations_from_dir("./transformations/workflows")

    # one call to multiple endpoint
    assert patched_put.call_count == 1


def test_component_import_directly_into_db(caplog, mocked_clean_test_db_session):
    response_mock = mock.Mock()
    response_mock.status_code = 200

    with caplog.at_level(logging.DEBUG):  # noqa: SIM117
        with mock.patch("hetdesrun.utils.requests.put", return_value=response_mock) as patched_put:
            caplog.clear()
            import_transformations_from_dir("./transformations/components", directly_into_db=True)
            assert "1946d5f8-44a8-724c-176f-16f3e49963af" in caplog.text
            # id of a component

    # did not try to upload via REST API
    assert patched_put.call_count == 0


def test_import_with_deprecate_older_versions(mocked_clean_test_db_session):
    response_mock = mock.Mock()
    response_mock.status_code = 201

    with mock.patch(  # noqa: SIM117
        "hetdesrun.utils.requests.put", return_value=response_mock
    ):
        with mock.patch(
            "hetdesrun.exportimport.importing.deprecate_all_but_latest_in_group",
            return_value=None,
        ) as patched_deprecate_group:
            import_transformations_from_dir(
                "./transformations/components",
                deprecate_older_revisions=True,
                directly_into_db=True,
            )

    assert patched_deprecate_group.call_count > 10


def test_generate_import_order_file_without_transform_py_to_json(tmp_path):
    download_path = tmp_path.joinpath("transformations")
    shutil.copytree("./transformations", download_path)

    response_mock = mock.Mock()
    response_mock.status_code = 201

    with mock.patch(  # noqa: SIM117
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as rest_api_mock:
        with mock.patch(
            "hetdesrun.exportimport.importing.deprecate_all_but_latest_in_group",
            return_value=None,
        ) as patched_deprecate_group:
            json_import_order = tmp_path.joinpath("json_import_order.txt")
            generate_import_order_file(str(download_path), str(json_import_order))

            assert patched_deprecate_group.call_count == 0
            assert rest_api_mock.call_count == 0
            assert os.path.exists(str(json_import_order))
            list_of_json_paths = []
            with open(json_import_order, "r", encoding="utf8") as file:  # noqa: UP015
                for line in file:
                    path = line[:-1]  # remove line break
                    list_of_json_paths.append(path)

            assert len(list_of_json_paths) > 100  # we have more than 100 json files
            assert not all(os.path.splitext(path)[1] == ".json" for path in list_of_json_paths)


def test_generate_import_order_file_with_transform_py_to_json(tmp_path):
    download_path = tmp_path.joinpath("transformations")
    shutil.copytree("./transformations", download_path)

    json_import_order = tmp_path.joinpath("json_import_order.txt")
    generate_import_order_file(
        str(download_path), str(json_import_order), transform_py_to_json=True
    )

    assert os.path.exists(str(json_import_order))
    list_of_json_paths = []
    with open(json_import_order, "r", encoding="utf8") as file:  # noqa: UP015
        for line in file:
            path = line[:-1]  # remove line break
            list_of_json_paths.append(path)
    assert len(list_of_json_paths) > 100  # we have more than 100 json files
    assert (
        str(
            download_path.joinpath(
                "components/time-length-operations/merge-timeseries"
                "-deduplicating-timestamps_100_b1dba357-b6d5-43cd-ac3e-7b6cd829be37.json"
            )
        )
    ) in list_of_json_paths


def test_import_importable():
    import_sources = list(get_import_sources("./tests/data/import_sources_examples"))

    dir_import_src = [imp_src for imp_src in import_sources if imp_src.is_dir][0]

    importable = load_import_source(dir_import_src)

    assert len(importable.transformation_revisions) > 0
    with mock.patch(
        "hetdesrun.exportimport.importing.update_or_create_single_transformation_revision",
        return_value=None,
    ) as mocked_update:
        import_importable(importable)

        mocked_update.assert_called_once()
        mocked_update.assert_any_call(
            mock.ANY,
            allow_overwrite_released=False,
            update_component_code=True,
            expand_component_code=False,
            strip_wiring=False,
            strip_wirings_with_adapter_ids=set(),
            keep_only_wirings_with_adapter_ids=set(),
            strip_release_wiring=False,
            strip_release_wirings_with_adapter_ids=set(),
            keep_only_release_wirings_with_adapter_ids=set(),
        )

        # Changing an option
        importable.import_config.update_config.allow_overwrite_released = True

        import_importables([importable])

        mocked_update.assert_any_call(
            mock.ANY,
            allow_overwrite_released=True,
            update_component_code=True,
            expand_component_code=False,
            strip_wiring=False,
            strip_wirings_with_adapter_ids=set(),
            keep_only_wirings_with_adapter_ids=set(),
            strip_release_wiring=False,
            strip_release_wirings_with_adapter_ids=set(),
            keep_only_release_wirings_with_adapter_ids=set(),
        )


@pytest.mark.parametrize(
    ("settings", "nof_entries", "expected_import_kwargs"),
    [
        ({}, 0, {}),
        ({}, 5, {"allow_overwrite_released": True}),
        ({"autodeploy_base_transformations": False}, 0, None),
        ({"autodeploy_base_transformations": False}, 5, None),
        ({"preserve_db_on_autodeploy": True}, 0, {}),
        ({"preserve_db_on_autodeploy": True}, 5, None),
        ({"autodeploy_allow_overwrite_released": False}, 0, {}),
        ({"autodeploy_allow_overwrite_released": False}, 5, {"allow_overwrite_released": False}),
    ],
)
def test_autodeploy_base_transformations(settings, nof_entries, expected_import_kwargs):
    settings = {
        "autodeploy_base_transformations": True,
        "preserve_db_on_autodeploy": False,
        "autodeploy_allow_overwrite_released": True,
        **settings,
    }
    with ExitStack() as stack:
        for name, value in settings.items():
            stack.enter_context(
                mock.patch(f"hetdesrun.webservice.config.runtime_config.{name}", value)
            )
        mocked_nof_db_entries = stack.enter_context(
            mock.patch("hetdesrun.exportimport.importing.nof_db_entries", return_value=nof_entries)
        )
        mocked_import = stack.enter_context(
            mock.patch("hetdesrun.exportimport.importing.import_transformations_from_dir")
        )
        autodeploy_base_transformations()

    if not settings["autodeploy_base_transformations"]:
        mocked_nof_db_entries.assert_not_called()

    if expected_import_kwargs is None:
        mocked_import.assert_not_called()
    else:
        mocked_import.assert_called_once_with(
            "./transformations/",
            directly_into_db=True,
            update_component_code=False,
            **expected_import_kwargs,
        )


def test_autoimport_at_backend_start(tmp_path, caplog):
    with mock.patch(
        "hetdesrun.exportimport.importing.autoimport_from_directory"
    ) as mocked_autoimport:
        with mock.patch("hetdesrun.webservice.config.runtime_config.autoimport_directory", ""):
            autoimport_at_backend_start()
        mocked_autoimport.assert_not_called()

        with (
            mock.patch(
                "hetdesrun.webservice.config.runtime_config.autoimport_directory", str(tmp_path)
            ),
            caplog.at_level(logging.WARNING),
        ):
            autoimport_at_backend_start()
        assert "HD_BACKEND_AUTOIMPORT_DIRECTORY" not in caplog.text
        mocked_autoimport.assert_called_once_with(str(tmp_path))


@pytest.mark.parametrize("missing", ["missing_dir", "a_file"])
def test_autoimport_at_backend_start_missing_dir(tmp_path, caplog, missing):
    (tmp_path / "a_file").write_text("")
    autoimport_dir = tmp_path / missing

    with (
        mock.patch(
            "hetdesrun.webservice.config.runtime_config.autoimport_directory", str(autoimport_dir)
        ),
        mock.patch(
            "hetdesrun.exportimport.importing.autoimport_from_directory"
        ) as mocked_autoimport,
        caplog.at_level(logging.WARNING),
    ):
        autoimport_at_backend_start()

    mocked_autoimport.assert_not_called()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.WARNING
    assert "set via HD_BACKEND_AUTOIMPORT_DIRECTORY does not exist" in caplog.text
    assert str(autoimport_dir) in caplog.text


def released_base_components(number: int) -> list[dict]:
    components = []
    for path in sorted(Path("./transformations/components").rglob("*.json")):
        trafo = json.loads(path.read_text())
        if trafo["state"] == "RELEASED" and "COMPONENT_INFO" in trafo["content"]:
            components.append(trafo)
        if len(components) == number:
            return components
    raise AssertionError("Not enough base components")


def write_autoimport_directory(directory: Path, components: list[dict]) -> None:
    """Import sources of all kinds, list.json with a config file filtering out components[2]"""
    (directory / "subdir" / "category").mkdir(parents=True)
    (directory / "subdir" / "category" / "c0.json").write_text(json.dumps(components[0]))
    (directory / "list.json").write_text(json.dumps([components[1], components[2]]))
    (directory / "list.json.config.json").write_text(
        json.dumps({"filter_params": {"names": [components[1]["name"]]}, "update_config": {}})
    )
    (directory / "single.json").write_text(json.dumps(components[3]))
    (directory / "c4.py").write_text(components[4]["content"])
    (directory / "broken.json").write_text("{")


def test_autoimport_from_directory(tmp_path, caplog, mocked_clean_test_db_session):
    components = released_base_components(5)
    write_autoimport_directory(tmp_path, components)

    with caplog.at_level(logging.ERROR):
        autoimport_from_directory(str(tmp_path))
    errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]

    # the broken import source does not prevent importing the others
    assert len(errors) == 1
    assert "Could not load import source" in errors[0]
    assert str(tmp_path / "broken.json") in errors[0]

    for index in (0, 1, 3, 4):
        assert (
            read_single_transformation_revision(components[index]["id"]).name
            == (components[index]["name"])
        )
    with pytest.raises(DBNotFoundError):  # filtered out via config file
        read_single_transformation_revision(components[2]["id"])


def test_autoimport_from_directory_import_configs(tmp_path, monkeypatch):
    components = released_base_components(5)
    write_autoimport_directory(tmp_path, components)
    (tmp_path / "broken.json").unlink()
    (tmp_path / "another.json").write_text(json.dumps(components[2]))
    (tmp_path / "another.json.config.json").write_text(
        json.dumps({"filter_params": {}, "update_config": {"strip_wirings": True}})
    )
    monkeypatch.setenv("HD_BACKEND_AUTOIMPORT_DIRECTORY_ALLOW_OVERWRITE_RELEASED", "true")
    monkeypatch.setenv("HD_BACKEND_AUTOIMPORT_DIRECTORY_UPDATE_COMPONENT_CODE", "false")

    with mock.patch("hetdesrun.exportimport.importing.import_importables") as mocked_import:
        autoimport_from_directory(str(tmp_path))

    importables = mocked_import.call_args.args[0]
    assert len(importables) == 3

    # import sources without config file together, following the environment variables
    assert {trafo.id for trafo in importables[0].transformation_revisions} == {
        UUID(components[index]["id"]) for index in (0, 3, 4)
    }
    assert importables[0].import_config.update_config.allow_overwrite_released is True
    assert importables[0].import_config.update_config.update_component_code is False

    # then the import sources with config file following it, in the order of their paths
    assert importables[1].import_config.update_config.strip_wirings is True
    assert importables[1].import_config.update_config.allow_overwrite_released is False
    assert importables[2].import_config.filter_params.names == [components[1]["name"]]
    assert importables[2].import_config.update_config.update_component_code is True
