import json
import logging
import os
from typing import Any, List, Optional, Tuple
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query, status
from pydantic import HttpUrl

from hetdesrun.backend.execution import (
    ExecByIdInput,
    ExecLatestByGroupIdInput,
    TrafoExecutionNotFoundError,
    TrafoExecutionResultValidationError,
    TrafoExecutionRuntimeConnectionError,
    execute_transformation_revision,
)
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.component.code import update_code
from hetdesrun.exportimport.utils import info
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.models.run import PerformanceMeasuredStep
from hetdesrun.persistence.dbservice.exceptions import (
    DBBadRequestError,
    DBIntegrityError,
    DBNotFoundError,
)
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    get_multiple_transformation_revisions,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


transformation_router = HandleTrailingSlashAPIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@transformation_router.post(
    "",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a transformation revision.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Successfully created the transformation revision"
        }
    },
)
async def create_transformation_revision(
    transformation_revision: TransformationRevision,
) -> TransformationRevision:
    """Store a transformation revision in the data base."""
    logger.info("create transformation revision %s", transformation_revision.id)

    if transformation_revision.type == Type.COMPONENT:
        logger.debug("transformation revision has type %s", Type.COMPONENT)
        transformation_revision.content = update_code(transformation_revision)
        logger.debug("generated code:\n%s", transformation_revision.content)

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created transformation revision")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


@transformation_router.get(
    "",
    response_model=List[TransformationRevision],
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns combined list of all transformation revisions (components and workflows)",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully got all transformation revisions"
        }
    },
)
async def get_all_transformation_revisions(
    type: Optional[Type] = Query(  # pylint: disable=redefined-builtin
        None,
        description="Filter for specified type",
    ),
    state: Optional[State] = Query(
        None,
        description="Filter for specified state",
    ),
    category: Optional[ValidStr] = Query(
        None,
        description="Filter for specified category",
    ),
    revision_group_id: Optional[UUID] = Query(
        None, description="Filter for specified revision group id"
    ),
    ids: Optional[List[UUID]] = Query(
        None,
        description="Filter for specified list of ids",
    ),
    names: Optional[List[NonEmptyValidStr]] = Query(
        None,
        description=("Filter for specified list of names"),
    ),
    include_dependencies: bool = Query(
        False,
        description=(
            "Set to True to additionally get those transformation revisions "
            "that the selected ones depend on"
        ),
    ),
    include_deprecated: bool = Query(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions"
        ),
    ),
    unused: bool = Query(
        False,
        description=(
            "Set to True to obtain only those transformation revisions that are "
            "not contained in workflows that do not have the state DISABLED."
        ),
    ),
) -> List[TransformationRevision]:
    """Get all transformation revisions from the data base.

    Used by frontend for initial loading of all transformations to populate the sidebar
    and to export selected transformation revisions.
    """

    msg = (
        "get all transformation revisions"
        + info(" of type ", type)
        + info(" in state ", state)
        + info(" in category ", category)
        + info(" with group_id ", revision_group_id)
        + info(
            " unless they are deprecated",
            include_deprecated,
            case=not include_deprecated,
        )
        + info(
            " that are unused",
            unused,
            case=unused,
        )
        + info("\nwith ids ", ids)
        + info("\nwith names ", names)
        + info(
            "\nand all dependency transformation revisions",
            include_dependencies,
            case=include_dependencies,
        )
    )

    logger.info(msg)

    try:
        transformation_revision_list = get_multiple_transformation_revisions(
            type=type,
            state=state,
            category=category,
            revision_group_id=revision_group_id,
            ids=ids,
            names=names,
            include_deprecated=include_deprecated,
            include_dependencies=include_dependencies,
            unused=unused,
        )
    except DBIntegrityError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"At least one entry in the DB is no valid transformation revision:\n{str(e)}",
        ) from e

    return transformation_revision_list


@transformation_router.get(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the transformation revision with the given id.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully got the transformation revision"
        }
    },
)
async def get_transformation_revision_by_id(
    # pylint: disable=redefined-builtin
    id: UUID = Path(
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> TransformationRevision:

    logger.info("get transformation revision %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(transformation_revision.json())

    return transformation_revision


def contains_deprecated(transformation_id: UUID) -> bool:
    logger.info(
        "check if transformation revision %s contains deprecated operators",
        str(transformation_id),
    )
    transformation_revision = read_single_transformation_revision(transformation_id)

    if transformation_revision.type is not Type.WORKFLOW:
        msg = f"transformation revision {id} is not a workflow!"
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    assert isinstance(transformation_revision.content, WorkflowContent)  # hint for mypy

    is_disabled = []
    for operator in transformation_revision.content.operators:
        logger.info(
            "operator with transformation id %s has status %s",
            str(operator.transformation_id),
            operator.state,
        )
        is_disabled.append(operator.state == State.DISABLED)

    return any(is_disabled)


def is_modifiable(
    existing_transformation_revision: Optional[TransformationRevision],
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = False,
) -> Tuple[bool, str]:
    if existing_transformation_revision is None:
        return True, ""
    if existing_transformation_revision.type != updated_transformation_revision.type:
        return False, (
            f"The type ({updated_transformation_revision.type}) of the "
            f"provided transformation revision does not\n"
            f"match the type ({existing_transformation_revision.type}) "
            f"of the stored transformation revision {existing_transformation_revision.id}!"
        )

    if (
        existing_transformation_revision.state == State.DISABLED
        and not allow_overwrite_released
    ):
        return False, (
            f"cannot modify deprecated transformation revision "
            f"{existing_transformation_revision.id}"
        )

    if (
        existing_transformation_revision.state == State.RELEASED
        and updated_transformation_revision.state != State.DISABLED
        and not allow_overwrite_released
    ):
        return False, (
            f"cannot modify released transformation revision "
            f"{existing_transformation_revision.id}"
        )

    return True, ""


def update_content(
    existing_transformation_revision: Optional[TransformationRevision],
    updated_transformation_revision: TransformationRevision,
) -> TransformationRevision:
    if updated_transformation_revision.type == Type.COMPONENT:
        updated_transformation_revision.content = update_code(
            updated_transformation_revision
        )
    elif existing_transformation_revision is not None:
        assert isinstance(
            existing_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        existing_operator_ids: List[UUID] = []
        for operator in existing_transformation_revision.content.operators:
            existing_operator_ids.append(operator.id)

        assert isinstance(
            updated_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        for operator in updated_transformation_revision.content.operators:
            if (
                operator.type == Type.WORKFLOW
                and operator.id not in existing_operator_ids
            ):
                operator.state = (
                    State.DISABLED
                    if contains_deprecated(operator.transformation_id)
                    else operator.state
                )
    return updated_transformation_revision


def if_applicable_release_or_deprecate(
    existing_transformation_revision: Optional[TransformationRevision],
    updated_transformation_revision: TransformationRevision,
) -> TransformationRevision:
    if existing_transformation_revision is not None:
        if (
            existing_transformation_revision.state == State.DRAFT
            and updated_transformation_revision.state == State.RELEASED
        ):
            logger.info(
                "release transformation revision %s",
                existing_transformation_revision.id,
            )
            updated_transformation_revision.release()
            # prevent overwriting content during releasing
            updated_transformation_revision.content = (
                existing_transformation_revision.content
            )
        if (
            existing_transformation_revision.state == State.RELEASED
            and updated_transformation_revision.state == State.DISABLED
        ):
            logger.info(
                "deprecate transformation revision %s",
                existing_transformation_revision.id,
            )
            updated_transformation_revision = TransformationRevision(
                **existing_transformation_revision.dict()
            )
            updated_transformation_revision.deprecate()
            # prevent overwriting content during deprecating
            updated_transformation_revision.content = (
                existing_transformation_revision.content
            )
    return updated_transformation_revision


@transformation_router.put(
    "/{id}",
    response_model=TransformationRevision,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates a transformation revision.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Successfully updated the transformation revision"
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Id from path does not match id from object in request body"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "DB entry is not modifyable due to status or none matching types"
        },
    },
)
async def update_transformation_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = Query(
        False, description="Only set to True for deployment"
    ),
    update_component_code: bool = Query(
        True, description="Only set to False for deployment"
    ),
) -> TransformationRevision:
    """Update or store a transformation revision in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    Unset attributes of the json sent in the request body will be set to default values,
    possibly changing the attribute saved in the DB.
    """

    logger.info("update transformation revision %s", id)

    if id != updated_transformation_revision.id:
        msg = (
            f"The id {id} does not match the id of the provided "
            f"transformation revision DTO {updated_transformation_revision.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)

    existing_transformation_revision: Optional[TransformationRevision] = None

    try:
        existing_transformation_revision = read_single_transformation_revision(
            id, log_error=False
        )
        logger.info("found transformation revision %s", id)
    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the transformation revision
        pass

    modifiable, msg = is_modifiable(
        existing_transformation_revision,
        updated_transformation_revision,
        allow_overwrite_released,
    )
    if not modifiable:
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    updated_transformation_revision = if_applicable_release_or_deprecate(
        existing_transformation_revision, updated_transformation_revision
    )

    if updated_transformation_revision.type == Type.WORKFLOW or update_component_code:
        updated_transformation_revision = update_content(
            existing_transformation_revision, updated_transformation_revision
        )

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision
            )
        )
        logger.info("updated transformation revision %s", id)
    except DBIntegrityError as e:
        logger.error(
            "integrity error in DB when trying to access entry for id %s\n%s", id, e
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        logger.error(
            "not found error in DB when trying to access entry for id %s\n%s", id, e
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(persisted_transformation_revision.json())

    return persisted_transformation_revision


@transformation_router.delete(
    "/{id}",
    summary="Deletes a transformation revision.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Successfully deleted the transformation revision"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Transformation revision is already released or deprecated"
        },
    },
)
async def delete_transformation_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    ignore_state: bool = Query(
        False,
        description=(
            "Set to true to enable deletion of released and deprecated transformation revisions"
        ),
    ),
) -> None:
    """Delete a transformation revision from the data base.

    Deleting a transformation revision is only possible if it is in state DRAFT.
    """

    logger.info("delete transformation revision %s", id)

    try:
        delete_single_transformation_revision(id, ignore_state=ignore_state)
        logger.info("deleted transformation revision %s", id)

    except DBBadRequestError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e)) from e

    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e


async def handle_trafo_revision_execution_request(
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:

    internal_full_measured_step = PerformanceMeasuredStep.create_and_begin(
        "internal_full"
    )
    if exec_by_id.job_id is None:
        exec_by_id.job_id = uuid4()

    try:
        exec_response = await execute_transformation_revision(exec_by_id)

    except TrafoExecutionNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    except TrafoExecutionRuntimeConnectionError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    except TrafoExecutionResultValidationError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    internal_full_measured_step.stop()
    exec_response.measured_steps.internal_full = internal_full_measured_step
    if get_config().advanced_performance_measurement_active:
        exec_response.process_id = os.getpid()
    return exec_response


@transformation_router.post(
    "/execute",
    response_model=ExecutionResponseFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Executes a transformation revision",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully executed the transformation revision"
        }
    },
)
async def execute_transformation_revision_endpoint(
    # pylint: disable=redefined-builtin
    exec_by_id: ExecByIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision.

    The transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    return await handle_trafo_revision_execution_request(exec_by_id)


callback_router = APIRouter()


@callback_router.post("{$callback_url}", response_model=ExecutionResponseFrontendDto)
def receive_execution_response(
    body: ExecutionResponseFrontendDto,  # pylint: disable=unused-argument
) -> None:
    pass


async def send_result_to_callback_url(
    callback_url: HttpUrl, result: ExecutionResponseFrontendDto
) -> None:
    headers = get_auth_headers()
    async with httpx.AsyncClient(
        verify=get_config().hd_backend_verify_certs,
        timeout=get_config().external_request_timeout,
    ) as client:
        try:
            await client.post(
                callback_url,
                headers=headers,
                json=json.loads(result.json()),  # TODO: avoid double serialization.
                # see https://github.com/samuelcolvin/pydantic/issues/1409 and
                # https://github.com/samuelcolvin/pydantic/issues/1409#issuecomment-877175194
            )
        except httpx.HTTPError as http_err:
            # handles both request errors (connection problems)
            # and 4xx and 5xx errors. See https://www.python-httpx.org/exceptions/
            msg = (
                f"Failure connecting to callback url ({callback_url}):\n{str(http_err)}"
            )
            logger.error(msg)
            # no re-raise reasonable, see comment in execute_and_post function


async def execute_and_post(exec_by_id: ExecByIdInput, callback_url: HttpUrl) -> None:
    # necessary general try-except block due to issue of starlette exception handler
    # overwriting uncaught exceptions https://github.com/tiangolo/fastapi/issues/2505
    try:
        try:
            result = await handle_trafo_revision_execution_request(exec_by_id)
            logger.info("Finished execution with job_id %s", str(exec_by_id.job_id))
        except HTTPException as http_exc:
            logger.error(
                "Execution with job id %s as background task failed:\n%s",
                str(exec_by_id.job_id),
                str(http_exc.detail),
            )
            # no re-raise reasonable due to issue mentioned above
        else:
            await send_result_to_callback_url(callback_url, result)
            logger.info(
                "Sent result of execution with job_id %s", str(exec_by_id.job_id)
            )
    except Exception as e:
        logger.error(
            "An unexpected error occurred during execution with job id %s as background task:\n%s",
            str(exec_by_id.job_id),
            str(e),
        )
        raise e


@transformation_router.post(
    "/execute-async",
    callbacks=callback_router.routes,
    summary="Executes a transformation revision asynchronously",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {"description": "Accepted execution request"},
    },
)
async def execute_asynchronous_transformation_revision_endpoint(
    exec_by_id: ExecByIdInput,
    background_tasks: BackgroundTasks,
    callback_url: HttpUrl = Query(
        ...,
        description="If provided execute asynchronous and post response to callback_url",
    ),
) -> Any:
    """Execute a transformation revision of asynchronously.

    A valid input is accepted with a corresponding response and the execution then runs in the
    background. The result of the execution is sent to the specified callback_url.
    You should have implemented an appropriate endpoint before using this one.

    The transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    background_tasks.add_task(execute_and_post, exec_by_id, callback_url)

    return {"message": f"Execution request with job id {exec_by_id.job_id} accepted"}


async def handle_latest_trafo_revision_execution_request(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
) -> ExecutionResponseFrontendDto:
    try:
        # pylint: disable=redefined-builtin
        id = get_latest_revision_id(exec_latest_by_group_id_input.revision_group_id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    exec_by_id_input = exec_latest_by_group_id_input.to_exec_by_id(id)

    return await handle_trafo_revision_execution_request(exec_by_id_input)


@transformation_router.post(
    "/execute-latest",
    response_model=ExecutionResponseFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Executes the latest transformation revision of a revision group",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully executed the latest transformation revision"
        }
    },
)
async def execute_latest_transformation_revision_endpoint(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
) -> ExecutionResponseFrontendDto:
    """Execute the latest transformation revision of a revision group.

    WARNING: Even when the input is not changed, the execution response might change if a new latest
    transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    calling this endpoint with the same payload as before will not work, but will result in errors.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """

    return await handle_latest_trafo_revision_execution_request(
        exec_latest_by_group_id_input
    )


async def execute_latest_and_post(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput, callback_url: HttpUrl
) -> None:
    # necessary general try-except block due to issue of starlette exception handler
    # overwriting uncaught exceptions https://github.com/tiangolo/fastapi/issues/2505
    try:
        try:
            result = await handle_latest_trafo_revision_execution_request(
                exec_latest_by_group_id_input
            )
            logger.info(
                "Finished execution with job_id %s",
                str(exec_latest_by_group_id_input.job_id),
            )
        except HTTPException as http_exc:
            logger.error(
                "Execution with job id %s as background task failed:\n%s",
                str(exec_latest_by_group_id_input.job_id),
                str(http_exc.detail),
            )
            # no re-raise reasonable due to issue mentioned above
        else:
            await send_result_to_callback_url(callback_url, result)
            logger.info(
                "Sent result of execution with job_id %s",
                str(exec_latest_by_group_id_input.job_id),
            )
    except Exception as e:
        logger.error(
            "An unexpected error occurred during execution with job_id %s as background task:\n%s",
            str(exec_latest_by_group_id_input.job_id),
            str(e),
        )
        raise e


@transformation_router.post(
    "/execute-latest-async",
    callbacks=callback_router.routes,
    summary="Executes the latest transformation revision of a revision group asynchronously",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        status.HTTP_202_ACCEPTED: {
            "description": "Accepted execution request for latest revision of revision group"
        },
    },
)
async def execute_asynchronous_latest_transformation_revision_endpoint(
    exec_latest_by_group_id_input: ExecLatestByGroupIdInput,
    background_tasks: BackgroundTasks,
    callback_url: HttpUrl = Query(
        ...,
        description="If provided execute asynchronous and post response to callback_url",
    ),
) -> Any:
    """Execute the latest transformation revision of a revision group asynchronously.

    WARNING: Even when the input is not changed, the execution response might change if a new latest
    transformation revision exists.

    WARNING: The inputs and outputs may be different for different revisions. In such a case,
    calling this endpoint with the same payload as before will not work, but will result in errors.

    A valid input is accepted with a corresponding response and the execution then runs in the
    background. The result of the execution is sent to the specified callback_url.
    You should have implemented an appropriate endpoint before using this one.

    The latest transformation will be determined by the released_timestamp of the released revisions
    of the revision group which are stored in the database.

    This transformation will be loaded from the DB and executed with the wiring sent in the request
    body.

    The test wiring will not be updated.
    """
    background_tasks.add_task(
        execute_latest_and_post, exec_latest_by_group_id_input, callback_url
    )

    return {
        "message": "Execution request for latest revision with "
        f"job id {exec_latest_by_group_id_input.job_id} accepted"
    }
