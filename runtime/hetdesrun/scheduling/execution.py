import datetime
import logging
from uuid import uuid4

from hetdesrun.backend.execution import (
    TrafoExecutionComponentAdapterComponentsNotFound,
    TrafoExecutionComponentImportCycleError,
    TrafoExecutionComponentImportsLoadingError,
    TrafoExecutionInputValidationError,
    TrafoExecutionNotFoundError,
    TrafoExecutionResultValidationError,
    TrafoExecutionRuntimeConnectionError,
    TrafoExecutionRuntimeHttpStatusError,
    perf_measured_execute_trafo_rev,
)
from hetdesrun.component.load import ComponentImportCycleError
from hetdesrun.models.execution import ExecByIdInput
from hetdesrun.persistence.dbmodels import ScheduledJobState
from hetdesrun.persistence.dbservice.schedule import (
    update_or_create_single_schedule_execution,
)
from hetdesrun.persistence.models.schedule import ScheduledJobInformation, ScheduleExecution
from hetdesrun.scheduling.scheduler import get_global_schedule_infos

logger = logging.getLogger(__name__)


async def execute_scheduled_transformation(  # noqa: PLR0915 PLR0912
    job_id: str, name: str
) -> ScheduledJobInformation | None:
    """Execution of scheduled transformation revisions job function"""
    schedule = get_global_schedule_infos().get(job_id, None)

    if schedule is None:  # pragma: no cover
        logger.error(
            "Missing schedule object for job %s with name %s. Cannot run. Aborting.", job_id, name
        )
        return None

    if schedule.transformation_id is None:  # pragma: no cover
        logger.error(
            "Missing schedule object for job %s with name %s. Cannot run. Aborting.", job_id, name
        )
        return None

    start_timestamp = datetime.datetime.now(datetime.UTC)

    exec_job_id = uuid4()
    exec_by_id = ExecByIdInput(
        job_id=exec_job_id,
        id=schedule.transformation_id,
        wiring=schedule.wiring,
        # plots should be generated, since past schedule execution results can be seen
        # in the ui via the result protocol viewer:
        run_pure_plot_operators=True,
    )

    scheduled_job_info = ScheduledJobInformation(
        state=ScheduledJobState.STARTED,
        schedule_job_id=str(job_id),
        schedule_name=name,
        trafo_exec_job_id=str(exec_job_id),
    )

    schedule_execution = ScheduleExecution(
        id=uuid4(),
        schedule_id=schedule.id,
        last_state_update=start_timestamp,
        start=start_timestamp,
        transformation_id=schedule.transformation_id,
        state=ScheduledJobState.STARTED,
        trafo_exec_job_id=exec_job_id,
        exec_input=exec_by_id,
    )

    update_or_create_single_schedule_execution(schedule_execution)

    try:
        exec_result = await perf_measured_execute_trafo_rev(exec_by_id, scheduling_internal=True)
    except TrafoExecutionInputValidationError as err:  # pragma: no cover
        msg = (
            "Could not validate execution input"
            f"\n{exec_by_id.model_dump_json(indent=2)}:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionNotFoundError as err:  # pragma: no cover
        msg = f"Could not find transformation revision {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except (  # pragma: no cover
        ComponentImportCycleError,
        TrafoExecutionComponentImportCycleError,
    ) as err:  # pragma: no cover
        msg = f"Detected component import cycle:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionComponentImportsLoadingError as err:  # pragma: no cover
        msg = f"Could not load some component import components:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionComponentAdapterComponentsNotFound as err:  # pragma: no cover
        msg = (
            "Could not find component revision for component adapter wirings or"
            " could not validate them as suitable component sources/sinks when"
            f" executing {exec_by_id.id}:\n{str(err)} with wiring\n{exec_by_id.wiring}."
            f" Exception was:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionRuntimeHttpStatusError as err:  # pragma: no cover
        # actually 4xx or 5xx
        msg = (
            f"Https status error during execution of transformation {exec_by_id.id} in external"
            f" runtime service:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionRuntimeConnectionError as err:  # pragma: no cover
        msg = f"Could not connect to runtime to execute transformation {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except TrafoExecutionResultValidationError as err:  # pragma: no cover
        msg = f"Could not validate execution result for transformation {exec_by_id.id}:\n{str(err)}"
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    except Exception as err:  # noqa: BLE001 # pragma: no cover
        msg = (
            f"ERROR: Generally uncaught exception during execution of "
            f"transformation {exec_by_id.id}:\n{str(err)}"
        )
        scheduled_job_info.state = ScheduledJobState.INVOCATION_ERROR
        scheduled_job_info.error_message = msg
        logger.error(msg)

    if scheduled_job_info.state != ScheduledJobState.INVOCATION_ERROR:
        if exec_result.error is None:
            scheduled_job_info.state = ScheduledJobState.SUCCESS
        else:
            if exec_result.error.type == "IntentionallyAbortedExecution":
                scheduled_job_info.state = ScheduledJobState.SKIPPED
            else:
                scheduled_job_info.state = ScheduledJobState.EXECUTION_ERROR
            scheduled_job_info.error_message = exec_result.error.message

        scheduled_job_info.exec_result = exec_result

    logger.info(
        "Scheduled job %s with name %s with trafo exec job id %s execution result: %s",
        job_id,
        name,
        exec_job_id,
        str(scheduled_job_info.state),
        extra={
            "scheduled_job_information": scheduled_job_info.model_dump(mode="json"),
        },
    )

    end_timestamp = datetime.datetime.now(datetime.UTC)

    schedule_execution.state = scheduled_job_info.state
    schedule_execution.error_message = scheduled_job_info.error_message
    schedule_execution.exec_result = scheduled_job_info.exec_result
    if schedule_execution.exec_result is not None:
        schedule_execution.transformation_name = schedule_execution.exec_result.tr_name
        schedule_execution.transformation_version_tag = schedule_execution.exec_result.tr_tag
    schedule_execution.last_state_update = end_timestamp
    schedule_execution.end = end_timestamp

    update_or_create_single_schedule_execution(schedule_execution)

    return scheduled_job_info
