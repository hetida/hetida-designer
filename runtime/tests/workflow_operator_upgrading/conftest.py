import os

import pytest

from hetdesrun.persistence.dbservice.revision import (
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.trafoutils.io.load import load_json


def add_trafo_comp(category, json_filename):
    path_to_json_file = os.path.join(
        "transformations",
        "components",
        category.lower(),
        json_filename,
    )
    tr_json = load_json(path_to_json_file)
    store_single_transformation_revision(TransformationRevision(**tr_json))


@pytest.fixture
def _all_pass_through_components(mocked_clean_test_db_session):
    add_trafo_comp("connectors", "pass-through_100_1946d5f8-44a8-724c-176f-16f3e49963af.json")
    add_trafo_comp(
        "connectors", "pass-through-series_100_bfa27afc-dea8-b8aa-4b15-94402f0739b6.json"
    )
    add_trafo_comp(
        "connectors", "pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json"
    )
