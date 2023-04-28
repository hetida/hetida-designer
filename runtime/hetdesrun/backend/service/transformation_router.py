import json
import logging
import os
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from fastapi.responses import HTMLResponse
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
from hetdesrun.exportimport.importing import (
    TrafoUpdateProcessSummary,
    import_importable,
)
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.models.run import PerformanceMeasuredStep
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    get_latest_revision_id,
    get_multiple_transformation_revisions,
    read_single_transformation_revision,
    store_single_transformation_revision,
    update_or_create_single_transformation_revision,
)
from hetdesrun.persistence.models.exceptions import ModelConstraintViolation
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.trafoutils.io.load import (
    Importable,
    ImportSourceConfig,
    MultipleTrafosUpdateConfig,
)
from hetdesrun.utils import State, Type
from hetdesrun.webservice.auth_dependency import get_auth_headers
from hetdesrun.webservice.auth_outgoing import ServiceAuthenticationError
from hetdesrun.webservice.config import get_config
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)


transformation_router = HandleTrailingSlashAPIRouter(
    prefix="/transformations",
    tags=["transformations"],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad Request"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_409_CONFLICT: {"description": "Conflict"},
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
    response_model=list[TransformationRevision],
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
    type: Type  # noqa: A002
    | None = Query(
        None,
        description="Filter for specified type",
    ),
    state: State
    | None = Query(
        None,
        description="Filter for specified state",
    ),
    category: ValidStr
    | None = Query(
        None,
        description="Filter for specified category",
    ),
    revision_group_id: UUID
    | None = Query(None, description="Filter for specified revision group id"),
    ids: list[UUID]
    | None = Query(
        None,
        description="Filter for specified list of ids",
    ),
    names: list[NonEmptyValidStr]
    | None = Query(
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
) -> list[TransformationRevision]:
    """Get all transformation revisions from the data base.

    Used by frontend for initial loading of all transformations to populate the sidebar
    and to export selected transformation revisions.
    """

    filter_params = FilterParams(
        type=type,
        state=state,
        category=category,
        revision_group_id=revision_group_id,
        ids=ids,
        names=names,
        include_dependencies=include_dependencies,
        include_deprecated=include_deprecated,
        unused=unused,
    )

    logger.info("get all transformation revisions with %s", repr(filter_params))

    try:
        transformation_revision_list = get_multiple_transformation_revisions(
            filter_params
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
    id: UUID = Path(  # noqa: A002
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
        raise HTTPException(status.HTTP_409_CONFLICT, detail=msg)

    assert isinstance(  # noqa: S101
        transformation_revision.content, WorkflowContent
    )  # hint for mypy

    is_disabled = []
    for operator in transformation_revision.content.operators:
        logger.info(
            "operator with transformation id %s has status %s",
            str(operator.transformation_id),
            operator.state,
        )
        is_disabled.append(operator.state == State.DISABLED)

    return any(is_disabled)


@transformation_router.put(
    "",
    status_code=status.HTTP_207_MULTI_STATUS,
    summary="Update (import) a list of transformation revisions",
    responses={
        status.HTTP_207_MULTI_STATUS: {
            "description": (
                "Processed request to update multiple transformation revisions. "
                "See response for details."
            )
        }
    },
)
async def update_transformation_revisions(
    updated_transformation_revisions: list[TransformationRevision],
    response: Response,
    type: Type  # noqa: A002
    | None = Query(
        None,
        description="Filter for specified type",
    ),
    state: State
    | None = Query(
        None,
        description="Filter for specified state",
    ),
    categories: list[ValidStr]
    | None = Query(None, description="Filter for categories", alias="category"),
    category_prefix: str
    | None = Query(
        None,
        description="Category prefix that must be matched exactly (case-sensitive).",
    ),
    revision_group_id: UUID
    | None = Query(None, description="Filter for specified revision group id"),
    ids: list[UUID]
    | None = Query(None, description="Filter for specified list of ids", alias="id"),
    names: list[NonEmptyValidStr]
    | None = Query(
        None, description=("Filter for specified list of names"), alias="name"
    ),
    include_deprecated: bool = Query(
        True,
        description=(
            "Set to False to omit transformation revisions with state DISABLED "
            "this will not affect included dependent transformation revisions"
        ),
    ),
    include_dependencies: bool = Query(
        True,
        description=(
            "Set to True to additionally import those transformation revisions "
            "of the provided trafos that the selected/filtered ones depend on."
        ),
    ),
    allow_overwrite_released: bool = Query(
        False, description="Only set to True for deployment"
    ),
    update_component_code: bool = Query(
        True, description="Only set to False for deployment"
    ),
    strip_wirings: bool = Query(
        False,
        description=(
            "Whether test wirings should be removed before importing."
            "This can be necessary if an adapter used in a test wiring is not "
            "available on this system."
        ),
    ),
    abort_on_error: bool = Query(
        False,
        description=(
            "If updating/creating fails for some trafo revisions and this setting is true,"
            " no attempt will be made to update/create the remaining trafo revs."
            " Note that the order in which updating/creating happens may differ from"
            " the ordering of the provided list since they are ordered by dependency"
            " relation before trying to process them. So it may be difficult to determine."
            " which trafos have been skipped / are missing and which have been successfully"
            " processed. Note that already processed actions will not be reversed."
        ),
    ),
    deprecate_older_revisions: bool = Query(
        False,
        description=(
            "Whether older revisions in the same trafo revision group should be deprecated."
            " If this is True, this is done for every revision group for which any trafo"
            " rev passes the filters and even for those that are included as dependencies"
            " via the include_dependencies property of the filter params!"
            " Note that this might not be done if abort_on_error is True and there is"
            " an error anywhere."
        ),
    ),
) -> dict[UUID, TrafoUpdateProcessSummary]:
    """Update/store multiple transformation revisions

    This updates or creates the given transformation revisions. Automatically
    determines correct order (by dependency / nesting) so that depending trafo
    revisions can be provided in arbitrary order to this endpoint.

    Returns detailed info about success/failure for each transformation revision.

    This endpoint can be used to import related sets of transformation revisions.
    Such a set does not have to be closed under dependency relation, e.g. elements
    of it can refer base components.
    """
    filter_params = FilterParams(
        type=type,
        state=state,
        categories=categories,
        category_prefix=category_prefix,
        revision_group_id=revision_group_id,
        ids=ids,
        names=names,
        include_deprecated=include_deprecated,
        include_dependencies=include_dependencies,
    )

    multi_import_config = MultipleTrafosUpdateConfig(
        allow_overwrite_released=allow_overwrite_released,
        update_component_code=update_component_code,
        strip_wirings=strip_wirings,
        abort_on_error=abort_on_error,
        deprecate_older_revisions=deprecate_older_revisions,
    )

    importable = Importable(
        transformation_revisions=updated_transformation_revisions,
        import_config=ImportSourceConfig(
            filter_params=filter_params, update_config=multi_import_config
        ),
    )

    success_per_trafo = import_importable(importable)
    response.status_code = status.HTTP_207_MULTI_STATUS

    return success_per_trafo


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
        status.HTTP_409_CONFLICT: {
            "description": "DB entry is not modifiable due to status or non-matching types"
        },
    },
)
async def update_transformation_revision(
    id: UUID,  # noqa: A002
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = Query(
        False, description="Only set to True for deployment"
    ),
    update_component_code: bool = Query(
        True, description="Only set to False for deployment"
    ),
    strip_wiring: bool = Query(False, description="Set to True to discard test wiring"),
) -> TransformationRevision:
    """Update or store a transformation revision in the database.

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

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision,
                allow_overwrite_released=allow_overwrite_released,
                update_component_code=update_component_code,
                strip_wiring=strip_wiring,
            )
        )
        logger.info("updated transformation revision %s", id)
    except DBIntegrityError as e:
        logger.error(
            "Integrity error in DB when trying to access entry for id %s\n%s", id, e
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        logger.error(
            "Not found error in DB when trying to access entry for id %s\n%s", id, e
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ModelConstraintViolation as e:
        logger.error("Update forbidden for transformation with id %s\n%s", id, e)
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e

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
        status.HTTP_409_CONFLICT: {
            "description": "Transformation revision is already released or deprecated"
        },
    },
)
async def delete_transformation_revision(
    id: UUID,  # noqa: A002
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

    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    except (ModelConstraintViolation, DBIntegrityError) as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e)) from e


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
    summary="Executes a transformation revision",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully executed the transformation revision"
        }
    },
)
async def execute_transformation_revision_endpoint(
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
    body: ExecutionResponseFrontendDto,  # noqa: ARG001
) -> None:
    pass


async def send_result_to_callback_url(
    callback_url: HttpUrl, result: ExecutionResponseFrontendDto
) -> None:
    try:
        headers = await get_auth_headers(external=True)
    except ServiceAuthenticationError as e:
        msg = (
            "Failed to get auth headers for sending result to callback url."
            f" Error was:\n{str(e)}"
        )
        logger.error(msg)

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
        id_ = get_latest_revision_id(exec_latest_by_group_id_input.revision_group_id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    exec_by_id_input = exec_latest_by_group_id_input.to_exec_by_id(id_)

    return await handle_trafo_revision_execution_request(exec_by_id_input)


@transformation_router.post(
    "/execute-latest",
    response_model=ExecutionResponseFrontendDto,
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


PLOT_TITLE_BAR_HEIGHT = 30
PLOT_AUTO_LAYOUT_VERTICAL_GAP = 10
PLOT_DEFAULT_HEIGHT = 200
PLOT_INNER_SIDE_PADDING = 5


def plotlyjson_to_html_div(name: str, plotly_json: Any, row: int = 0) -> str:
    plotly_json["layout"]["autosize"] = True
    plotly_json["layout"]["width"] = "100%"
    plotly_json["layout"]["height"] = "100%"

    return f"""
    <div class="resize-drag" style="position:absolute;top:{
        str(row*(200 + PLOT_TITLE_BAR_HEIGHT + PLOT_AUTO_LAYOUT_VERTICAL_GAP + PLOT_INNER_SIDE_PADDING))+"px"
        };left:0;padding:0px;margin:0px;
        margin-top:0px;height:240px;width:100%
        ;padding-left:10px;padding-right:10px;padding-bottom:5px">
        <div class="handle" style="padding-left:{str(PLOT_INNER_SIDE_PADDING)}px;user-select:none">
            {name}
        </div>

        <div style="width:100%;height:calc(100% - {str(PLOT_TITLE_BAR_HEIGHT + PLOT_INNER_SIDE_PADDING*2)}px)">
            <div style="width:100%;height:100%">

                <!-- the div on which Plotly works (which it somehow "rewrites"): -->
                <div id="{name}" style="width:100%;height:100%"></div>
                <script>
                    Plotly.newPlot("{name}", {json.dumps(plotly_json)} )
                    //initial resize:
                    Plotly.Plots.resize("{name}")
                </script>
            </div>
        </div>
    </div>
    """


def dashboard_title(trafo: TransformationRevision) -> str:
    return trafo.name + " " + trafo.version_tag + " (" + trafo.state + ")"


@transformation_router.get(
    "/{id}/dashboard",
    summary="A dashboard generated from the transformation and its test wiring.",
    status_code=status.HTTP_200_OK,
    response_class=HTMLResponse,
    responses={
        status.HTTP_200_OK: {"description": "Successfully generated dashboard"},
    },
)
async def transformation_dashboard(
    id: UUID = Path(  # noqa: A002
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> str:
    """Dashboard fed by transformation revision plot outputs

    Generates a html page containing the result plots in movable and resizable
    rectangles, i.e. an elementary dashboard.
    """

    logger.info("get transformation revision %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    logger.debug(transformation_revision.json())

    exec_by_id: ExecByIdInput = ExecByIdInput(
        id=id,
        wiring=None,  # so execution will default to the stored test wiring!
        run_pure_plot_operators=True,
    )

    exec_resp: ExecutionResponseFrontendDto = (
        await handle_trafo_revision_execution_request(exec_by_id)
    )

    plotly_outputs = {
        name: exec_resp.output_results_by_output_name[name]
        for name in exec_resp.output_results_by_output_name
        if exec_resp.output_types_by_output_name[name] == "PLOTLYJSON"
    }

    dashboard_html = (
        r"""
    <!DOCTYPE html>
    <html style="height:100%">

    <script src="https://cdn.plot.ly/plotly-2.18.2.min.js" charset="utf-8"></script>
    <script type="module">
    import interact from 
    'https://cdn.interactjs.io/v1.10.11/interactjs/index.js'

    function dragMoveListener (event) {
    var target = event.target
    // keep the dragged position in the data-x/data-y attributes
    var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx
    var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy

    // translate the element
    target.style.transform = 'translate(' + x + 'px, ' + y + 'px)'

    // update the posiion attributes
    target.setAttribute('data-x', x)
    target.setAttribute('data-y', y)
    }

    // this function is used later in the resizing and gesture demos
    window.dragMoveListener = dragMoveListener

    var gridTarget = interact.snappers.grid({
    // can be a pair of x and y, left and top,
    // right and bottom, or width, and height
    x: 20,
    y: 20,

        offset: {x: 0, y: 0}

    // optional
    /*
    range: 10,

    // optional
    offset: { x: 5, y: 10 },
        
    // optional
    limits: {
        top: 0,
        left: 0,
        bottom: 500,
        height: 500
    }
    */
    })


    interact('.resize-drag')
    .resizable({
        // resize from all edges and corners
        edges: { left: true, right: true, bottom: true, top: true },
        margin:4, // edge thickness for resizing, see https://github.com/taye/interact.js/issues/685
        listeners: {
        move (event) {
            var target = event.target
            var x = (parseFloat(target.getAttribute('data-x')) || 0)
            var y = (parseFloat(target.getAttribute('data-y')) || 0)

            // update the element's style
            target.style.width = event.rect.width + 'px'
            target.style.height = event.rect.height + 'px'

            // translate when resizing from top or left edges
            x += event.deltaRect.left
            y += event.deltaRect.top

            target.style.transform = 'translate(' + x + 'px,' + y + 'px)'

            target.setAttribute('data-x', x)
            target.setAttribute('data-y', y)
            //target.textContent = Math.round(event.rect.width) + '\u00D7' + Math.round(event.rect.height)
            //console.log(target.firstElementChild);
            // here plotly content should be triggered a redraw/adaption to new size?? Instead of setting textContent
    //target.firstElementChild.redraw()
                Plotly.Plots.resize(target.getElementsByTagName('div')[1].firstElementChild.firstElementChild)
            
        }
        },
        restrictEdges: {
                outer: "parent"
        },
        restrictSize: {
                min: { width: 100, height: 50 }
        },
        origin: 'parent',    
        snap: {
        // snap targets pay attention to the action's origin option
        targets: [
            interact.createSnapGrid({
            x: 10,
            y: 10,
            })
        ],
        relativePoints: [
            { x: 0, y: 0 }
        ]
        },    
        /*
        modifiers: [
        // keep the edges inside the parent
        interact.modifiers.restrictEdges({
            outer: 'parent'
        }),

        // minimum size
        interact.modifiers.restrictSize({
            min: { width: 100, height: 50 }
        }),
        
        //interact.modifiers.snap({ targets: [gridTarget] })
        ],
        */

        inertia: true
    })
    .draggable({
        allowFrom: ".handle",
        origin: 'parent',    
        snap: {
        // snap targets pay attention to the action's origin option
        targets: [
            interact.createSnapGrid({
            x: 10,
            y: 10,
            })
        ],
        relativePoints: [
            { x: 0, y: 0 }
        ]
        },
        restrict: {
        // restrictions *don't* pay attention to the action's origin option
        // so using 'parent' for both origin and restrict.restriction works
        restriction: 'parent',
        elementRect: {top: 0, left: 0, bottom: 0, right: 1}
        },    
        listeners: { move: window.dragMoveListener },
        inertia: true,
        /*
        modifiers: [
        interact.modifiers.restrictRect({
            restriction: 'parent',
            //endOnly: true //instead of:
            elementRect: {top: 0, left: 0, bottom: 0, right: 1}
        })
        ]
        */
    })
    </script>
    <head>
    <style>
    .resize-drag {
    width: 400px;
    height: 150px;
    border-radius: 4px;
    padding: 5px;
    margin: 3px;
    background-color: #29e;
    color: white;
    font-size: 20px;
    font-family: sans-serif;
    opacity: .8;

    touch-action: none;

    /* This makes things *much* easier */
    box-sizing: border-box;
    }

    </style>
    </head>
    <body style="height:100%;padding=10px">


    """  # noqa: ISC003
        + """<div style="color:black;font-size:28px;font-family:sans-serif;text-align:center">"""
        + f"""{dashboard_title(transformation_revision)}</div>"""
        + r"""
    <div style="background-color:lightgrey;width:100%;height:100%;
        position:relative;top:0;left:0;padding:0px;margin:0px;
        overflow-y:auto">

    """
        + "\n".join(
            (
                plotlyjson_to_html_div(name, plotly_json, row=ind)
                for ind, (name, plotly_json) in enumerate(plotly_outputs.items())
            )
        )
        + r"""
    </div>
    </body>

    """
    )
    print(dashboard_html)
    print(len(plotly_outputs))
    return dashboard_html
