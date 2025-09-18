"""Test logging in component code"""

import json
import logging
import os

import pytest
from structlog.stdlib import ProcessorFormatter

from hetdesrun import logger as hetdesrun_runtime_exec_logger
from hetdesrun.component.load import base_module_path
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.runtime import runtime_execution_logger
from hetdesrun.runtime.logging import (
    ComponentCodeLogHandler,
    ExecutionContextFilter,
    JobIdContextFilter,
)
from hetdesrun.trafoutils.trafo_collection import TrafoCollection


@pytest.fixture
def example_exec_input(mocked_clean_test_db_session):
    with TrafoCollection(save_to_db=True) as tc:
        logging_component = tc.add_from_py_file(
            os.path.join(
                "tests",
                "data",
                "components",
                "logging_in_component.py",
            )
        )

    return ExecByIdInput(
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
async def test_logging_in_component(async_test_client, example_exec_input, caplog):
    """Test that exec context information gets into log records and in exec response

    Together with the test below that tests the formatter, this tests guarantees
    about the infos being contained in log records ensures that
    context information is actually logged.
    """
    exec_input = example_exec_input

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


def check_for_correct_filters(
    logger: logging.Logger, log_execution_context: bool = False, log_job_id_context: bool = False
):
    """Test that the correct filters are attached to a logging handler."""
    non_component_code_handlers = [
        handler for handler in logger.handlers if not isinstance(handler, ComponentCodeLogHandler)
    ]

    assert len(non_component_code_handlers) == 1

    handler = non_component_code_handlers[0]
    formatter = handler.formatter

    assert isinstance(formatter, ProcessorFormatter)

    handler_filters = handler.filters

    has_execution_context_filter = any(
        isinstance(f, ExecutionContextFilter) for f in handler_filters
    )
    has_job_id_context_filter = any(isinstance(f, JobIdContextFilter) for f in handler_filters)

    assert has_execution_context_filter == log_execution_context, (
        "Execution context filter not present"
    )
    assert has_job_id_context_filter == log_job_id_context, "Job ID context filter not present"


def get_log_records_for_logger(
    records: list[logging.LogRecord], logger: logging.Logger
) -> list[logging.LogRecord]:
    """Extract only those records emitted by `logger` or its children."""
    name = logger.name
    return [r for r in records if r.name == name or r.name.startswith(name + ".")]


def check_log_formatting(
    logger: logging.Logger,
    log_records: list[logging.LogRecord],
    log_execution_context: bool = False,
    log_job_id_context: bool = False,
):
    """Test that the formatter attached to a given logging handler works correctly."""

    # This assumes that only one handler with a ProcessorFormatter is attached to each logger
    structlog_handlers = [h for h in logger.handlers if isinstance(h.formatter, ProcessorFormatter)]
    assert structlog_handlers, "No handler with a ProcessorFormatter found"
    assert len(structlog_handlers) == 1, "More than one handler with a ProcessorFormatter found"

    formatter = structlog_handlers[0].formatter

    # Fields that should always appear in the logs
    shared_fields = ("timestamp", "level", "logger", "filename", "lineno", "func_name", "message")

    for log_record in log_records:
        formatted_record = formatter.format(log_record)  # type: ignore[union-attr]
        assert all(k in formatted_record for k in shared_fields), (
            "Not all shared fields are present"
        )
        if log_job_id_context or log_execution_context:
            assert "job_id" in formatted_record, "The job ID is not present"

        if log_execution_context:
            execution_context_fields = ("tr_id", "tr_name", "tr_tag", "tr_type", "op_id", "op_name")
            assert all(k in formatted_record for k in execution_context_fields), (
                "Not all execution context fields are present"
            )


@pytest.mark.asyncio
async def test_logging_configuration_formatting_setup(
    async_test_client, example_exec_input, caplog
):
    """Test that formatting is configured correctly for several loggers

    Together with the test above that tests the records, this guarantees
    that context informartion is actually logged.
    """
    exec_input = example_exec_input

    with caplog.at_level(logging.DEBUG):
        caplog.clear()

        async with async_test_client as ac:
            resp = await ac.post(
                "/api/transformations/execute", json=json.loads(exec_input.model_dump_json())
            )

        assert resp.status_code == 200

    test_cases = [
        (logging.getLogger(base_module_path), True, False),
        (runtime_execution_logger, True, False),
        (hetdesrun_runtime_exec_logger, True, False),
        (logging.getLogger("hetdesrun"), False, False),
        (logging.getLogger("hetdesrun_runtime_service"), False, True),
    ]

    for logger, execution_context, job_context in test_cases:
        check_for_correct_filters(
            logger, log_execution_context=execution_context, log_job_id_context=job_context
        )

        recs = get_log_records_for_logger(caplog.records, logger)
        check_log_formatting(
            logger, recs, log_execution_context=execution_context, log_job_id_context=job_context
        )
