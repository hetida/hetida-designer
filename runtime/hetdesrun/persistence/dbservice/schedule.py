import datetime
import logging
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.models.schedule import (
    Schedule,
    ScheduleDBModel,
    ScheduleExecution,
    ScheduleExecutionDBModel,
)

logger = logging.getLogger(__name__)


def add_schedule(session: SQLAlchemySession, schedule: Schedule) -> None:
    try:
        db_model = schedule.to_orm_model()
        session.add(db_model)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store schedule "
            f"with id {schedule.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def update_schedule(session: SQLAlchemySession, schedule: Schedule) -> None:
    try:
        db_model = schedule.to_orm_model()

        session.execute(
            update(ScheduleDBModel)
            .where(ScheduleDBModel.id == db_model.id)
            .values(
                name=db_model.name,
                active=db_model.active,
                cron_expression=db_model.cron_expression,
                transformation_id=db_model.transformation_id,
                wiring=db_model.wiring,
            )
        )

    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to update "
            f"schedule with id {schedule.id}.\n"
            f"Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_schedule(
    schedule: Schedule,
) -> None:
    with get_session()() as session, session.begin():
        add_schedule(session, schedule)


def update_or_create_single_schedule(schedule: Schedule) -> Schedule:
    with get_session()() as session, session.begin():
        try:
            select_schedule_by_id(session, schedule.id, log_error=False)
        except DBNotFoundError:
            add_schedule(session, schedule)
        else:
            update_schedule(session, schedule)

        return select_schedule_by_id(session, schedule.id)


def select_schedule_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> Schedule:
    result = session.execute(
        select(ScheduleDBModel).where(ScheduleDBModel.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no schedule in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return Schedule.from_orm_model(result)


def read_single_schedule(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> Schedule:
    with get_session()() as session, session.begin():
        return select_schedule_by_id(session, id, log_error)


def select_multiple_schedules() -> list[Schedule]:
    with get_session()() as session, session.begin():
        selection = select(ScheduleDBModel)
        results = session.execute(selection).scalars().all()

        return [Schedule.from_orm_model(result) for result in results]


def get_multiple_schedules() -> list[Schedule]:
    """Selection of schedules from db"""
    schedule_list = select_multiple_schedules()
    return schedule_list


def delete_schedule(session: SQLAlchemySession, schedule_id: UUID) -> None:
    try:
        session.execute(delete(ScheduleDBModel).where(ScheduleDBModel.id == schedule_id))
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to delete schedule "
            f"with id {schedule_id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def delete_single_schedule(id: UUID) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        delete_schedule(session, id)


# Schedule Executions


def add_schedule_execution(
    session: SQLAlchemySession, schedule_execution: ScheduleExecution
) -> None:
    try:
        db_model = schedule_execution.to_orm_model()
        session.add(db_model)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store schedule execution"
            f"with id {schedule_execution.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def update_schedule_execution(
    session: SQLAlchemySession, schedule_execution: ScheduleExecution
) -> None:
    try:
        db_model = schedule_execution.to_orm_model()

        session.execute(
            update(ScheduleExecutionDBModel)
            .where(ScheduleExecutionDBModel.id == db_model.id)
            .values(
                schedule_id=db_model.schedule_id,
                last_state_update=db_model.last_state_update,
                start=db_model.start,
                end=db_model.end,
                transformation_id=db_model.transformation_id,
                transformation_name=db_model.transformation_name,
                transformation_version_tag=db_model.transformation_version_tag,
                transformation_type=db_model.transformation_type,
                transformation_state=db_model.transformation_state,
                state=db_model.state,
                trafo_exec_job_id=db_model.trafo_exec_job_id,
                exec_result=db_model.exec_result,
                error_message=db_model.error_message,
            )
        )

    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to update "
            f"schedule execution with id {schedule_execution.id}.\n"
            f"Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_schedule_execution(
    schedule_execution: ScheduleExecution,
) -> None:
    with get_session()() as session, session.begin():
        add_schedule_execution(session, schedule_execution)


def update_or_create_single_schedule_execution(
    schedule_execution: ScheduleExecution,
) -> ScheduleExecution:
    with get_session()() as session, session.begin():
        try:
            select_schedule_execution_by_id(session, schedule_execution.id, log_error=False)
        except DBNotFoundError:
            add_schedule_execution(session, schedule_execution)
        else:
            update_schedule_execution(session, schedule_execution)

        return select_schedule_execution_by_id(session, schedule_execution.id)


def select_schedule_execution_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ScheduleExecution:
    result = session.execute(
        select(ScheduleExecutionDBModel).where(ScheduleExecutionDBModel.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no schedule execution in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return ScheduleExecution.from_orm_model(result)


def read_single_schedule_execution(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> ScheduleExecution:
    with get_session()() as session, session.begin():
        return select_schedule_execution_by_id(session, id, log_error)


def select_latest_schedule_execution_by_schedule_id(
    session: SQLAlchemySession,
    schedule_id: UUID,
    exclude_exec_result: bool = False,
    exclude_exec_input: bool = False,
) -> ScheduleExecution | None:
    result = session.execute(
        select(ScheduleExecutionDBModel)
        .where(ScheduleExecutionDBModel.schedule_id == schedule_id)
        .order_by(ScheduleExecutionDBModel.last_state_update.desc())
        .limit(1)
    ).scalar_one_or_none()
    if result is None:
        return None
    if exclude_exec_result:
        result.exec_result = None
    if exclude_exec_input:
        result.exec_input = None
    return ScheduleExecution.from_orm_model(result)


def read_latest_schedule_execution_by_schedule_id(
    schedule_id: UUID,  # noqa: A002
    exclude_exec_result: bool = False,
    exclude_exec_input: bool = False,
) -> ScheduleExecution | None:
    with get_session()() as session, session.begin():
        return select_latest_schedule_execution_by_schedule_id(
            session, schedule_id, exclude_exec_result, exclude_exec_input
        )


def select_multiple_schedule_executions(
    exclude_exec_result: bool = False,
    exclude_exec_input: bool = False,
    schedule_id: UUID | None = None,
) -> list[ScheduleExecution]:
    with get_session()() as session, session.begin():
        selection = select(
            *(
                (
                    ScheduleExecutionDBModel.id,
                    ScheduleExecutionDBModel.schedule_id,
                    ScheduleExecutionDBModel.last_state_update,
                    ScheduleExecutionDBModel.start,
                    ScheduleExecutionDBModel.end,
                    ScheduleExecutionDBModel.transformation_id,
                    ScheduleExecutionDBModel.transformation_name,
                    ScheduleExecutionDBModel.transformation_version_tag,
                    ScheduleExecutionDBModel.transformation_type,
                    ScheduleExecutionDBModel.transformation_state,
                    ScheduleExecutionDBModel.state,
                    ScheduleExecutionDBModel.trafo_exec_job_id,
                    ScheduleExecutionDBModel.error_message,
                )
                + ((ScheduleExecutionDBModel.exec_result,) if not exclude_exec_result else ())
                + ((ScheduleExecutionDBModel.exec_input,) if not exclude_exec_input else ())
            )
        )

        if schedule_id is not None:
            selection = selection.where(ScheduleExecutionDBModel.schedule_id == schedule_id)

        results = session.execute(selection).all()

        return [
            ScheduleExecution.from_orm_model(
                ScheduleExecutionDBModel(
                    id=row.id,
                    schedule_id=row.schedule_id,
                    last_state_update=row.last_state_update,
                    start=row.start,
                    end=row.end,
                    transformation_id=row.transformation_id,
                    transformation_name=row.transformation_name,
                    transformation_version_tag=row.transformation_version_tag,
                    transformation_type=row.transformation_type,
                    transformation_state=row.transformation_state,
                    state=row.state,
                    trafo_exec_job_id=row.trafo_exec_job_id,
                    exec_result=None if exclude_exec_result else row.exec_result,
                    exec_input=None if exclude_exec_input else row.exec_input,
                    error_message=row.error_message,
                )
            )
            for row in results
        ]


def get_multiple_schedule_executions(
    exclude_exec_result: bool = False,
    exclude_exec_input: bool = False,
    schedule_id: UUID | None = None,
) -> list[ScheduleExecution]:
    """Selection of schedules from db"""
    return select_multiple_schedule_executions(
        exclude_exec_result=exclude_exec_result,
        exclude_exec_input=exclude_exec_input,
        schedule_id=schedule_id,
    )


def select_latest_schedule_executions_per_schedule(
    exclude_exec_result: bool = False,
    exclude_exec_input: bool = False,
    schedule_id: UUID | None = None,
) -> list[ScheduleExecution]:
    with get_session()() as session, session.begin():
        base_query = select(
            *(
                (
                    ScheduleExecutionDBModel.id,
                    ScheduleExecutionDBModel.schedule_id,
                    ScheduleExecutionDBModel.last_state_update,
                    ScheduleExecutionDBModel.start,
                    ScheduleExecutionDBModel.end,
                    ScheduleExecutionDBModel.transformation_id,
                    ScheduleExecutionDBModel.transformation_name,
                    ScheduleExecutionDBModel.transformation_version_tag,
                    ScheduleExecutionDBModel.transformation_type,
                    ScheduleExecutionDBModel.transformation_state,
                    ScheduleExecutionDBModel.state,
                    ScheduleExecutionDBModel.trafo_exec_job_id,
                    ScheduleExecutionDBModel.error_message,
                )
                + ((ScheduleExecutionDBModel.exec_result,) if not exclude_exec_result else ())
                + ((ScheduleExecutionDBModel.exec_input,) if not exclude_exec_input else ())
            )
        )

        if schedule_id is not None:
            base_query = base_query.where(ScheduleExecutionDBModel.schedule_id == schedule_id)

        subquery = base_query.add_columns(
            func.row_number()
            .over(
                partition_by=ScheduleExecutionDBModel.schedule_id,
                order_by=ScheduleExecutionDBModel.last_state_update.desc(),
            )
            .label("rn")
        ).subquery()

        results = session.execute(select(subquery).where(subquery.c.rn == 1)).mappings().all()

        return [
            ScheduleExecution.from_orm_model(
                ScheduleExecutionDBModel(
                    id=row.id,
                    schedule_id=row.schedule_id,
                    last_state_update=row.last_state_update,
                    start=row.start,
                    end=row.end,
                    transformation_id=row.transformation_id,
                    transformation_name=row.transformation_name,
                    transformation_version_tag=row.transformation_version_tag,
                    transformation_type=row.transformation_type,
                    transformation_state=row.transformation_state,
                    state=row.state,
                    trafo_exec_job_id=row.trafo_exec_job_id,
                    exec_result=None if exclude_exec_result else row.exec_result,
                    exec_input=None if exclude_exec_input else row.exec_input,
                    error_message=row.error_message,
                )
            )
            for row in results
        ]


def get_latest_schedule_executions(exclude_exec_result: bool = False) -> list[ScheduleExecution]:
    """Selection of schedules from db"""
    return select_latest_schedule_executions_per_schedule(
        exclude_exec_result=exclude_exec_result,
    )


def delete_schedule_execution(session: SQLAlchemySession, schedule_execution_id: UUID) -> None:
    try:
        session.execute(
            delete(ScheduleExecutionDBModel).where(
                ScheduleExecutionDBModel.id == schedule_execution_id
            )
        )
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to delete schedule execution "
            f"with id {schedule_execution_id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def delete_single_schedule_execution(id: UUID) -> None:  # noqa: A002
    with get_session()() as session, session.begin():
        delete_schedule_execution(session, id)


def delete_schedule_executions(session: SQLAlchemySession, older_than: datetime.datetime) -> None:
    try:
        session.execute(
            delete(ScheduleExecutionDBModel).where(
                ScheduleExecutionDBModel.last_state_update <= older_than
            )
        )
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to delete old schedule executions "
            f"older than {older_than}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def delete_old_schedule_executions(older_than: datetime.datetime) -> None:
    with get_session()() as session, session.begin():
        delete_schedule_executions(session, older_than)
