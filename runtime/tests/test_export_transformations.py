import json
import os
from unittest import mock

from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto
from hetdesrun.exportimport.export import (
    export_transformations,
)
from hetdesrun.persistence.models.transformation import TransformationRevision

root_path = "./transformations/"
json_files = [
    "components/arithmetic/consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json",
    "components/basic/filter_100_18260aab-bdd6-af5c-cac1-7bafde85188f.json",
    "components/basic/greater-or-equal_100_f759e4c0-1468-0f2e-9740-41302b860193.json",
    "components/basic/last-datetime-index_100_c8e3bc64-b214-6486-31db-92a8888d8991.json",
    "components/basic/restrict-to-time-interval_100_bf469c0a-d17c-ca6f-59ac-9838b2ff67ac.json",
    "components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
    "components/connectors/pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
    "components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
    "components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
    "components/remaining-useful-life/univariate-linear-rul-regression_100_8d61a267-3a71-51cd-2817-48c320469d6b.json",
    "components/visualization/single-timeseries-plot_100_8fba9b51-a0f1-6c6c-a6d4-e224103b819c.json",
    "components/visualization/univariate-linear-rul-regression-result-plot_100_9c3f88ce-1311-241e-18b7-acf7d3f5a051.json",
    "workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json",
    "workflows/examples/univariate-linear-rul-regression-example_100_806df1b9-2fc8-4463-943f-3d258c569663.json",
    "workflows/examples/linear-rul-from-last-positive-step_100_3d504361-e351-4d52-8734-391aa47e8f24.json",
]

tr_json_list = []

for file_path in json_files:
    with open(root_path + file_path, encoding="utf8") as f:
        tr_json = json.load(f)
    tr_json_list.append(tr_json)

tr_json_dict = {}

for tr_json in tr_json_list:
    tr_json_dict[tr_json["id"]] = tr_json


def test_export_all_transformations(tmp_path):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_json_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:
        export_transformations(tmp_path)

        assert mocked_get.call_count == 1
        _, args, _ = mocked_get.mock_calls[0]
        assert "transformations" in args[0]

        exported_paths = []
        for root, _, files in os.walk(tmp_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == len(json_files)

        for file_path in json_files:
            assert str(tmp_path.joinpath(file_path)) in exported_paths


def test_export_all_transformations_components_as_code(tmp_path):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_json_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:
        export_transformations(tmp_path, components_as_code=True, expand_component_code=True)

        assert mocked_get.call_count == 1
        _, args, _ = mocked_get.mock_calls[0]
        assert "transformations" in args[0]

        exported_paths = []
        for root, _, files in os.walk(tmp_path):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))
                if ext == ".py":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == len(json_files)

        for file_path in json_files[:-3]:
            assert str(tmp_path.joinpath(file_path)).replace(".json", ".py") in exported_paths
        for file_path in json_files[-3:]:
            assert str(tmp_path.joinpath(file_path)) in exported_paths


bi_list = []

for file_path in json_files:
    with open(root_path + file_path, encoding="utf8") as f:
        tr = TransformationRevision(**json.load(f))
        bi = TransformationRevisionFrontendDto.from_transformation_revision(tr)
        bi_json = json.loads(bi.json())
    bi_list.append(bi_json)


def mock_get_trafo_from_java_backend(id, type, headers):  # noqa: A002,
    return TransformationRevision(**tr_json_dict[str(id)])


def test_export_all_base_items(tmp_path):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=bi_list)

    with mock.patch(  # noqa: SIM117
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:
        with mock.patch(
            "hetdesrun.exportimport.export.get_transformation_from_java_backend",
            new=mock_get_trafo_from_java_backend,
        ):
            export_transformations(tmp_path, java_backend=True)

            assert mocked_get.call_count == 1
            _, args, _ = mocked_get.mock_calls[0]
            assert "base-items" in args[0]

            exported_paths = []
            for root, _, files in os.walk(tmp_path):
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext == ".json":
                        exported_paths.append(os.path.join(root, file))

            assert len(exported_paths) == len(json_files)

            for file_path in json_files:
                assert str(tmp_path.joinpath(file_path)) in exported_paths
