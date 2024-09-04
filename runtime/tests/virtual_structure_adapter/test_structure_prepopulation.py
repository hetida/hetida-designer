from unittest import mock

import pytest

from hetdesrun.adapters.virtual_structure_adapter.utils import prepopulate_structure
from hetdesrun.structure.db.orm_service import load_structure_from_json_file
from hetdesrun.structure.structure_service import is_database_empty


def test_with_prepopulation_disabled(mocked_clean_test_db_session):
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config.prepopulate_virtual_structure_adapter_at_designer_startup",
        False,
    ):
        prepopulate_structure()

    # Verify that no changes have been made to the database
    assert is_database_empty()


@pytest.mark.usefixtures("_fill_db")
def test_if_existing_structure_is_overwritten_if_specified():
    with mock.patch.multiple(  # noqa: SIM117
        "hetdesrun.webservice.config.runtime_config",
        prepopulate_virtual_structure_adapter_at_designer_startup=True,
        completely_overwrite_an_existing_virtual_structure_at_hd_startup=True,
        structure_to_prepopulate_virtual_structure_adapter=load_structure_from_json_file(
            "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.virtual_structure_adapter.utils.delete_structure"
        ) as mocked_delete:
            prepopulate_structure()
            mocked_delete.assert_called_once()
