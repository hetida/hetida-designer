import json
import os
from copy import deepcopy
from unittest import mock
from uuid import UUID

from hetdesrun.backend.models.component import ComponentRevisionFrontendDto
from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.exportimport.export import (
    export_transformations,
    get_transformation_from_java_backend,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import Type

root_path = "./transformations"
json_files = [
    "/components/arithmetic/consecutive-differences_100_ce801dcb-8ce1-14ad-029d-a14796dcac92.json",
    "/components/basic/filter_100_18260aab-bdd6-af5c-cac1-7bafde85188f.json",
    "/components/basic/greater-or-equal_100_f759e4c0-1468-0f2e-9740-41302b860193.json",
    "/components/basic/last-datetime-index_100_c8e3bc64-b214-6486-31db-92a8888d8991.json",
    "/components/basic/restrict-to-time-interval_100_bf469c0a-d17c-ca6f-59ac-9838b2ff67ac.json",
    "/components/connectors/pass-through-float_100_2f511674-f766-748d-2de3-ad5e62e10a1a.json",
    "/components/connectors/pass-through-integer_100_57eea09f-d28e-89af-4e81-2027697a3f0f.json",
    "/components/connectors/pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json",
    "/components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json",
    "/components/remaining-useful-life/univariate-linear-rul-regression_100_8d61a267-3a71-51cd-2817-48c320469d6b.json",
    "/components/visualization/single-timeseries-plot_100_8fba9b51-a0f1-6c6c-a6d4-e224103b819c.json",
    "/components/visualization/univariate-linear-rul-regression-result-plot_100_9c3f88ce-1311-241e-18b7-acf7d3f5a051.json",
    "/workflows/examples/data-from-last-positive-step_100_2cbb87e7-ea99-4404-abe1-be550f22763f.json",
    "/workflows/examples/univariate-linear-rul-regression-example_100_806df1b9-2fc8-4463-943f-3d258c569663.json",
    "/workflows/examples/linear-rul-from-last-positive-step_100_3d504361-e351-4d52-8734-391aa47e8f24.json",
]

tr_list = []

for file_path in json_files:
    with open(root_path + file_path, encoding="utf-8") as f:
        tr_json = json.load(f)
    tr_list.append(tr_json)

tr_dict = {}

for tr_json in tr_list:
    tr_dict[tr_json["id"]] = tr_json


def test_export_all_transformations(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(tmpdir)

        assert mocked_get.call_count == 1
        _, args, _ = mocked_get.mock_calls[0]
        assert "transformations" in args[0]

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == len(json_files)

        for file_path in json_files:
            assert tmpdir.join(file_path) in exported_paths


bi_list = []

for file_path in json_files:
    with open(root_path + file_path, encoding="utf-8") as f:
        tr = TransformationRevision(**json.load(f))
        bi = TransformationRevisionFrontendDto.from_transformation_revision(tr)
        bi_json = json.loads(bi.json())
    bi_list.append(bi_json)


def java_backend_mock(url, *args, **kwargs):
    call_infos_from_url = url.rsplit("/", 3)
    bi_id = call_infos_from_url[-1]
    endpoint = call_infos_from_url[-2]

    response_mock = mock.Mock()
    response_mock.status_code = 200

    if endpoint == "components":
        dto = ComponentRevisionFrontendDto.from_transformation_revision(
            TransformationRevision(**tr_dict[bi_id])
        )
        response_mock.json = mock.Mock(return_value=json.loads(dto.json(by_alias=True)))

    if endpoint == "workflows":
        dto = WorkflowRevisionFrontendDto.from_transformation_revision(
            TransformationRevision(**tr_dict[bi_id])
        )
        response_mock.json = mock.Mock(return_value=json.loads(dto.json(by_alias=True)))

    if endpoint == "documentations":
        response_mock.json = mock.Mock(
            return_value={"document": tr_dict[bi_id]["documentation"]}
        )

    return response_mock


def test_get_transformation_from_java_backend():
    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        new=java_backend_mock,
    ):
        tr_id_str = "18260aab-bdd6-af5c-cac1-7bafde85188f"
        tr_from_dict = tr_dict[tr_id_str]
        tr_from_backend = get_transformation_from_java_backend(
            UUID(tr_id_str), Type.COMPONENT
        )

        # released timestamp cannot be the same
        # it is not set for java backend objects
        #  and set to "now" during conversion
        del tr_from_backend["released_timestamp"]
        del tr_from_dict["released_timestamp"]

        assert tr_from_backend == tr_from_dict


def mock_get_trafo_from_java_backend(id, type):
    return tr_dict[str(id)]


def test_export_all_base_items(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=bi_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:
        with mock.patch(
            "hetdesrun.exportimport.export.get_transformation_from_java_backend",
            new=mock_get_trafo_from_java_backend,
        ):

            export_transformations(tmpdir, java_backend=True)

            assert mocked_get.call_count == 1
            _, args, _ = mocked_get.mock_calls[0]
            assert "base-items" in args[0]

            exported_paths = []
            for root, _, files in os.walk(tmpdir):
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext == ".json":
                        exported_paths.append(os.path.join(root, file))

            assert len(exported_paths) == len(json_files)

            for file_path in json_files:
                assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_filtered_by_type(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(tmpdir, type="COMPONENT")

        assert mocked_get.call_count == 1
        _, args, _ = mocked_get.mock_calls[0]
        assert "transformations" in args[0]

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 12

        for file_path in json_files[:12]:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_filtered_by_state(tmpdir):
    tr_list_state = deepcopy(tr_list)
    tr_list_state[0]["state"] = "DRAFT"
    tr_list_state[1]["state"] = "DRAFT"
    tr_list_state[-1]["state"] = "DISABLED"
    tr_list_state[-2]["state"] = "DISABLED"
    tr_list_state[-3]["state"] = "DISABLED"
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list_state)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(tmpdir, state="DRAFT")

        assert mocked_get.call_count == 1

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 2

        for file_path in json_files[:2]:
            assert tmpdir.join(file_path) in exported_paths

        export_transformations(tmpdir, state="RELEASED")

        assert mocked_get.call_count == 2

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        # increased by ten more exported JSON files
        assert len(exported_paths) == 12

        for file_path in json_files[:-3]:
            assert tmpdir.join(file_path) in exported_paths

        export_transformations(tmpdir, state="DISABLED")

        assert mocked_get.call_count == 3

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        # increased by three more exported JSON file
        assert len(exported_paths) == 15

        for file_path in json_files:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_filtered_by_category(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(tmpdir, category="Basic")

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 4

        for file_path in json_files[1:5]:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_filtered_by_names_and_tags(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(
            tmpdir,
            names_and_tags=[("Filter", "1.0.0"), ("Consecutive differences", "1.0.0")],
        )

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 2

        for file_path in json_files[:2]:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_filtered_by_ids(tmpdir):
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(
            tmpdir,
            ids=[
                "ce801dcb-8ce1-14ad-029d-a14796dcac92",
                "18260aab-bdd6-af5c-cac1-7bafde85188f",
            ],
        )

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 2

        for file_path in json_files[:2]:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_without_deprecated(tmpdir):
    tr_list_state = deepcopy(tr_list)
    tr_list_state[-1]["state"] = "DISABLED"
    tr_list_state[-2]["state"] = "DRAFT"
    tr_list_state[-3]["state"] = "DRAFT"
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list_state)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(tmpdir, include_deprecated=False)

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 14

        for file_path in json_files[:-1]:
            assert tmpdir.join(file_path) in exported_paths


def test_export_transformations_combined_filters(tmpdir):
    tr_list_state = deepcopy(tr_list)
    tr_list_state[-1]["state"] = "DISABLED"
    resp_mock = mock.Mock()
    resp_mock.status_code = 200
    resp_mock.json = mock.Mock(return_value=tr_list_state)

    with mock.patch(
        "hetdesrun.exportimport.export.requests.get",
        return_value=resp_mock,
    ) as mocked_get:

        export_transformations(
            tmpdir,
            category="Basic",
            names_and_tags=[("Filter", "1.0.0"), ("Consecutive differences", "1.0.0")],
        )

        assert mocked_get.call_count == 1

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 1

        for file_path in json_files[1:2]:
            assert tmpdir.join(file_path) in exported_paths

        export_transformations(tmpdir, type="WORKFLOW", include_deprecated=False)

        assert mocked_get.call_count == 2

        exported_paths = []
        for root, _, files in os.walk(tmpdir):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext == ".json":
                    exported_paths.append(os.path.join(root, file))

        assert len(exported_paths) == 13

        for file_path in json_files[:-5]:
            assert tmpdir.join(file_path) in exported_paths

        for file_path in json_files[-4:-1]:
            assert tmpdir.join(file_path) in exported_paths
