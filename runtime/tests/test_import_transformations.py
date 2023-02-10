import logging
import os
import shutil
from unittest import mock

from hetdesrun.exportimport.importing import (
    generate_import_order_file,
    import_importable,
    import_importables,
    import_transformations,
    update_or_create_transformation_revision,
)
from hetdesrun.persistence import sessionmaker
from hetdesrun.persistence.dbservice.revision import read_single_transformation_revision
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

    tr_json = transformation_revision_from_python_code(code)

    tr = TransformationRevision(**tr_json)

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


def test_import_single_transformation(clean_test_db_engine):
    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.Session",
        sessionmaker(clean_test_db_engine),
    ):
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

    with caplog.at_level(logging.DEBUG):  # noqa: SIM117

        with mock.patch(
            "hetdesrun.utils.requests.put", return_value=response_mock
        ) as patched_put:
            caplog.clear()
            import_transformations("./transformations/components")
            assert "Reduce data set by leaving out values" in caplog.text
            # name of a component

    # at least tries to upload many components (we have more than 10 there)
    assert patched_put.call_count > 10

    # Test logging when posting does not work
    response_mock.status_code = 400

    with caplog.at_level(logging.INFO):  # noqa: SIM117
        with mock.patch(
            "hetdesrun.utils.requests.put", return_value=response_mock
        ) as patched_put:
            caplog.clear()
            import_transformations("./transformations/components")
            assert "COULD NOT PUT COMPONENT" in caplog.text


def test_workflow_import_via_rest_api(caplog):
    response_mock = mock.Mock()
    response_mock.status_code = 200

    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        import_transformations("./transformations/workflows")

    # at least tries to upload many workflows
    assert patched_put.call_count > 3
    # Test logging when posting does not work
    response_mock.status_code = 400
    with mock.patch(
        "hetdesrun.utils.requests.put", return_value=response_mock
    ) as patched_put:
        caplog.clear()
        import_transformations("./transformations/workflows")
        assert "COULD NOT PUT WORKFLOW" in caplog.text


def test_component_import_directly_into_db(caplog, clean_test_db_engine):
    patched_session = sessionmaker(clean_test_db_engine)
    with mock.patch(  # noqa: SIM117
        "hetdesrun.persistence.dbservice.nesting.Session",
        patched_session,
    ):
        with mock.patch(
            "hetdesrun.persistence.dbservice.revision.Session",
            patched_session,
        ):
            response_mock = mock.Mock()
            response_mock.status_code = 200

            with caplog.at_level(logging.DEBUG):  # noqa: SIM117

                with mock.patch(
                    "hetdesrun.utils.requests.put", return_value=response_mock
                ) as patched_put:
                    caplog.clear()
                    import_transformations(
                        "./transformations/components", directly_into_db=True
                    )
                    assert "1946d5f8-44a8-724c-176f-16f3e49963af" in caplog.text
                    # id of a component

            # did not try to upload via REST API
            assert patched_put.call_count == 0


def test_import_with_deprecate_older_versions():
    response_mock = mock.Mock()
    response_mock.status_code = 201

    with mock.patch(  # noqa: SIM117
        "hetdesrun.utils.requests.put", return_value=response_mock
    ):
        with mock.patch(
            "hetdesrun.exportimport.importing.deprecate_all_but_latest_in_group",
            return_value=None,
        ) as patched_deprecate_group:

            import_transformations(
                "./transformations/components", deprecate_older_revisions=True
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
            assert len(list_of_json_paths) == 143
            assert all(
                os.path.splitext(path)[1] == ".json" for path in list_of_json_paths
            )


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
    assert len(list_of_json_paths) == 147
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
            strip_wiring=False,
        )

        # Changing an option
        importable.import_config.update_config.allow_overwrite_released = True

        import_importables([importable])

        mocked_update.assert_any_call(
            mock.ANY,
            allow_overwrite_released=True,
            update_component_code=True,
            strip_wiring=False,
        )
