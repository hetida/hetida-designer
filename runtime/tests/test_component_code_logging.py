"""Test logging in component code"""

import json
import logging
import os

import pytest

from hetdesrun import logger as hetdesrun_runtime_exec_logger
from hetdesrun.component.load import base_module_path
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.runtime import runtime_execution_logger
from hetdesrun.runtime.logging import ComponentCodeLogHandler
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


def assert_infos_in_record(
    record: logging.LogRecord,
    log_execution_context: bool = False,
    log_job_id_context: bool = False,
):
    if log_job_id_context or log_execution_context:
        assert str(record.currently_executed_job_id) == "bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb"
    else:
        assert not hasattr(record, "currently_executed_job_id")

    if log_execution_context:
        assert (
            str(record.currently_executed_transformation_id)
            == "abafbb92-3cdf-45a4-98ad-c72d9cf0b705"
        )

        assert str(record.currently_executed_transformation_name) == "Test logging"
        assert str(record.currently_executed_transformation_tag) == "0.1.0"
        assert str(record.currently_executed_transformation_type) == "COMPONENT"
        assert hasattr(record, "currently_executed_operator_hierarchical_id")
        assert hasattr(record, "currently_executed_operator_hierarchical_name")
    else:
        assert not hasattr(record, "currently_executed_transformation_id")
        assert not hasattr(record, "currently_executed_transformation_name")
        assert not hasattr(record, "currently_executed_transformation_tag")
        assert not hasattr(record, "currently_executed_transformation_type")
        assert not hasattr(record, "currently_executed_operator_hierarchical_id")
        assert not hasattr(record, "currently_executed_operator_hierarchical_name")


def extract_single_record_with_msg_containing(
    log_records: list[logging.LogRecord], contained_str: str
) -> logging.LogRecord:
    filtered_records = [rec for rec in log_records if contained_str in rec.message]
    assert len(filtered_records) > 0
    return filtered_records[0]


@pytest.mark.asyncio
async def test_logging_in_component(async_test_client, mocked_clean_test_db_session, caplog):
    """Test that exec context information gets into log records and in exec response

    Together with the test below that tests the formatter, this tests guarantees
    about the infos being contained in log records ensures that
    context information is actually logged.
    """
    with TrafoCollection(save_to_db=True) as tc:
        logging_component = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "logging_in_component.py",
            )
        )

    exec_input = ExecByIdInput(
        id=logging_component.id,
        job_id="bbbbbbbb-3cdf-45a4-98ad-bbbbbbbbbbbb",
        wiring=WorkflowWiring(
            input_wirings=[
                {
                    "workflow_input_name": "new_input_1",
                    "adapter_id": "direct_provisioning",
                    "filters": {"value": "test_string"},
                }
            ]
        ),
    )

    with caplog.at_level(logging.DEBUG):
        caplog.clear()

        async with async_test_client as ac:
            resp = await ac.post(
                "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
            )

        assert resp.status_code == 200

        resp_json = resp.json()

        # Log messages occur in execution response
        assert len(resp_json["gathered_component_code_logs"]) == 3

        # tr id in log message in execution response
        assert (
            resp_json["gathered_component_code_logs"][0]["tr_id"]
            == "abafbb92-3cdf-45a4-98ad-c72d9cf0b705"
        )

        log_record = extract_single_record_with_msg_containing(
            caplog.records, "TEST LOGGING COMPONENT WITH COMPONENT MODULE LOGGER"
        )
        assert_infos_in_record(log_record, True, True)

        log_record = extract_single_record_with_msg_containing(
            caplog.records, "TEST LOGGING hetdesrun_runtime_exec_logger"
        )
        assert_infos_in_record(log_record, True, False)

        log_record = extract_single_record_with_msg_containing(
            caplog.records, "TEST LOGGING runtime_execution_logger"
        )
        assert_infos_in_record(log_record, True, True)

        log_record = extract_single_record_with_msg_containing(
            caplog.records, "TEST LOGGING hetdesrun module logger"
        )
        assert_infos_in_record(log_record, False, False)


def log_format_assertions(
    logger: logging.Logger, log_execution_context: bool = False, log_job_id_context: bool = False
):
    """Test that formatting is configured correctly so that context is logged if there

    Together with the test above that tests the records, this guarantees
    that context informartion is actually logged.
    """

    non_component_code_handlers = [
        handler for handler in logger.handlers if not isinstance(handler, ComponentCodeLogHandler)
    ]

    assert len(non_component_code_handlers) == 1

    handler = non_component_code_handlers[0]
    assert handler.formatter is not None

    formatter = handler.formatter

    if log_execution_context or log_job_id_context:
        assert "%(currently_executed_job_id)" in formatter._fmt
    else:
        assert "%(currently_executed_job_id)" not in formatter._fmt

    if log_execution_context:
        assert "%(currently_executed_transformation_type)" in formatter._fmt
        assert "%(currently_executed_transformation_id)" in formatter._fmt
        assert "%(currently_executed_transformation_name)" in formatter._fmt
        assert "%(currently_executed_transformation_tag)" in formatter._fmt
        assert "%(currently_executed_operator_hierarchical_id)" in formatter._fmt
        assert "%(currently_executed_operator_hierarchical_name)" in formatter._fmt
    else:
        assert "%(currently_executed_transformation_type)" not in formatter._fmt
        assert "%(currently_executed_transformation_id)" not in formatter._fmt
        assert "%(currently_executed_transformation_name)" not in formatter._fmt
        assert "%(currently_executed_transformation_tag)" not in formatter._fmt
        assert "%(currently_executed_operator_hierarchical_id)" not in formatter._fmt
        assert "%(currently_executed_operator_hierarchical_name)" not in formatter._fmt


def test_logging_configuration_formatting_setup():
    """Test that formatting is configured correctly for several loggers"""

    logger = logging.getLogger(base_module_path)

    log_format_assertions(logger, True, True)

    log_format_assertions(runtime_execution_logger, True, True)

    log_format_assertions(hetdesrun_runtime_exec_logger, True, False)

    log_format_assertions(logging.getLogger("hetdesrun"), False, False)

    log_format_assertions(logging.getLogger("hetdesrun_runtime_service"), False, True)
