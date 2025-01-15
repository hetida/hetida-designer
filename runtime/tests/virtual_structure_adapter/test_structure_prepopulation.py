import json
from unittest import mock

import pytest

from hetdesrun.adapters.virtual_structure_adapter.config import VirtualStructureAdapterConfig
from hetdesrun.adapters.virtual_structure_adapter.structure_prepopulation import (
    prepopulate_structure,
)
from hetdesrun.structure.db.structure_service import load_structure_from_json_file
from hetdesrun.structure.models import CompleteStructure


@pytest.mark.usefixtures("_fill_db")
def test_if_existing_structure_is_overwritten_if_specified():
    with mock.patch.multiple(  # noqa: SIM117
        "hetdesrun.adapters.virtual_structure_adapter.config.vst_adapter_config",
        prepopulate_virtual_structure_adapter_at_designer_startup=True,
        completely_overwrite_an_existing_virtual_structure_at_hd_startup=True,
        structure_to_prepopulate_virtual_structure_adapter=load_structure_from_json_file(
            "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
        ),
    ):
        with mock.patch(
            "hetdesrun.adapters.virtual_structure_adapter.structure_prepopulation.delete_structure"
        ) as mocked_delete:
            prepopulate_structure()
            mocked_delete.assert_called_once()


def test_validator_filepath_must_be_set_when_populating_from_file():
    with pytest.raises(
        ValueError,
        match="structure_filepath_to_prepopulate_virtual_structure_adapter must be set "
        "if prepopulate_virtual_structure_adapter_via_file is set to True",
    ):
        _ = VirtualStructureAdapterConfig(
            prepopulate_virtual_structure_adapter_at_designer_startup=True,
            prepopulate_virtual_structure_adapter_via_file=True,
        )


def test_validator_structure_must_be_provided_if_populating_from_env_var():
    with pytest.raises(
        ValueError,
        match="structure_to_prepopulate_virtual_structure_adapter must be set "
        "if prepopulate_virtual_structure_adapter_at_designer_startup is set to True "
        "and you want to populate from an environment variable",
    ):
        _ = VirtualStructureAdapterConfig(
            prepopulate_virtual_structure_adapter_at_designer_startup=True,
        )


def test_validator_complete_structure_must_not_be_set_if_populating_from_file():
    file_path = "tests/virtual_structure_adapter/data/simple_end_to_end_test.json"
    with open(file_path) as file:
        structure_json = json.load(file)
    complete_structure = CompleteStructure(**structure_json)
    with pytest.raises(
        ValueError,
        match="structure_to_prepopulate_virtual_structure_adapter must NOT be set "
        "if prepopulate_virtual_structure_adapter_via_file is set to True, "
        "since you wish to populate from a file",
    ):
        _ = VirtualStructureAdapterConfig(
            prepopulate_virtual_structure_adapter_via_file=True,
            structure_filepath_to_prepopulate_virtual_structure_adapter="nf",
            structure_to_prepopulate_virtual_structure_adapter=complete_structure,
        )
