import logging
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.models.schedule import Schedule, ScheduleDBModel

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
        msg = f"Found no transformation revision in database with id {id}"
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
