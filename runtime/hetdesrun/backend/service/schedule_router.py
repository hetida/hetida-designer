import logging
from uuid import UUID

from fastapi import HTTPException, status

from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.schedule import (
    delete_single_schedule,
    get_multiple_schedules,
    read_single_schedule,
    store_single_schedule,
    update_or_create_single_schedule,
)
from hetdesrun.persistence.models.schedule import Schedule
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

schedule_router = HandleTrailingSlashAPIRouter(
    prefix="/schedules",
    tags=["schedules"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)

logger = logging.getLogger(__name__)


@schedule_router.post(
    "",
    response_model=Schedule,
    response_model_exclude_none=True,
    summary="Creates a schedule.",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_201_CREATED: {"description": "Successfully created the schedule"}},
)
async def create_schedule(schedule: Schedule) -> Schedule:
    """Store a Schedule in the database"""
    logger.info("create schedule %s", schedule.id)

    try:
        store_single_schedule(schedule)
    except DBIntegrityError as err:
        msg = f"Could not store schedule {schedule.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    try:
        persisted_schedule = read_single_schedule(schedule.id)
    except DBNotFoundError as err:
        msg = f"Could not find schedule {schedule.id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    return persisted_schedule


@schedule_router.get(
    "",
    response_model=list[Schedule],
    summary="Returns all schedules",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got all schedules"}},
)
async def get_all_schedules() -> list[Schedule]:
    try:
        schedule_list = get_multiple_schedules()
    except DBIntegrityError as err:
        msg = f"At least one entry in the DB is no valid transformation revision:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    return schedule_list


@schedule_router.put(
    "/{id}",
    response_model=Schedule,
    summary="Updates a schedule.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully updated the schedule"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Id from path does not match id from object in request body"
        },
    },
)
async def update_schedule(
    id: UUID,  # noqa: A002
    updated_schedule: Schedule,
) -> Schedule:
    """Update a schedule

    Creates schedule if it does not exist already (Upsert).
    """
    logger.info("update schedule %s", id)

    if id != updated_schedule.id:
        msg = f"The id {id} does not match the id of the provided schedule {updated_schedule.id}"
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=msg)

    try:
        persisted_schedule = update_or_create_single_schedule(updated_schedule)
    except DBIntegrityError as err:
        msg = f"Integrity error in DB when trying to access entry for id {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err

    return persisted_schedule


@schedule_router.delete(
    "/{id}",
    summary="Deletes a schedule.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_204_NO_CONTENT: {"description": "Successfully deleted the schedule"}},
)
async def delete_schedule(
    id: UUID,  # noqa: A002
) -> None:
    """Delete a schedule from the database."""

    logger.info("delete schedule %s", id)

    try:
        delete_single_schedule(id)
        logger.info("deleted schedule %s", id)

    except DBNotFoundError as err:
        msg = f"Could not find schedule {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg) from err

    except DBIntegrityError as err:
        msg = f"Could not delete schedule {id}:\n{str(err)}"
        logger.error(msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg) from err
