import json
from unittest import mock

import pytest

from hetdesrun.backend.execution import prepare_execution_input
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import cache_conditionally


def test_basic_caching() -> None:
    @cache_conditionally(lambda num: num > 42)
    def squaring(base_num):
        return base_num**2

    assert squaring.cache_ is not None
    assert squaring.cache_ == {}

    _ = squaring(10)

    assert squaring.cache_ == {10: 100}

    _ = squaring(4)

    assert squaring.cache_ == {10: 100}


@pytest.mark.asyncio
async def test_basic_caching_with_async_func() -> None:
    async def calculation(num):
        return num**2

    @cache_conditionally(lambda num: num > 42)
    async def squaring(base_num):
        square = await calculation(base_num)
        return square

    assert squaring.cache_ is not None
    assert squaring.cache_ == {}

    _ = await squaring(12)

    assert squaring.cache_ == {12: 144}

    _ = await squaring(6)

    assert squaring.cache_ == {12: 144}


@pytest.fixture(scope="function")  # noqa: PT003
def enable_caching_in_config():
    with mock.patch(
        "hetdesrun.webservice.config.runtime_config",
        enable_caching_for_non_draft_trafos_for_execution=True,
    ) as _fixture:
        yield _fixture


@pytest.fixture()
def _db_with_sample_trafos(mocked_clean_test_db_session):
    # Load a transformation revision with state RELEASED
    with open(
        "transformations/components/connectors/pass-through-string_100_2b1b474f-ddf5-1f4d-fec4-17ef9122112b.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))

    # Load a transformation revision with state DRAFT
    with open(
        "tests/data/components/pass-through-string_100_draft_d28bcb31-2254-4987-9862-75773e55884f.json"
    ) as f:
        trafo_data = json.load(f)
    store_single_transformation_revision(TransformationRevision(**trafo_data))


def test_trafo_caching(enable_caching_in_config, _db_with_sample_trafos):  # noqa: PT019
    # Create an execution object for a released trafo revision
    exec_by_id_input = ExecByIdInput(
        id="2b1b474f-ddf5-1f4d-fec4-17ef9122112b",
        wiring={
            "input_wirings": [
                {
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "Test exec"},
                    "use_default_value": False,
                    "workflow_input_name": "input",
                }
            ],
            "output_wirings": [],
        },
        run_pure_plot_operators=False,
    )

    with mock.patch(
        "hetdesrun.persistence.dbservice.revision.read_single_transformation_revision",
        mock.Mock(side_effect=read_single_transformation_revision),
    ) as db_load_patch:
        # DB should only be accessed on the first function call
        _ = prepare_execution_input(exec_by_id_input)
        db_load_patch.assert_called_once()
        _ = prepare_execution_input(exec_by_id_input)
        db_load_patch.assert_called_once()

        # Set ID to that of a draft trafo
        exec_by_id_input.id = "d28bcb31-2254-4987-9862-75773e55884f"

        # DB should be accessed on both function calls
        _ = prepare_execution_input(exec_by_id_input)
        _ = prepare_execution_input(exec_by_id_input)
        assert db_load_patch.call_count == 3
