from typing import List
import logging

from uuid import UUID, uuid4
import json

import httpx
from fastapi import APIRouter, Path, status, HTTPException

from posixpath import join as posix_urljoin

from pydantic import ValidationError

from hetdesrun.utils import Type, State, get_auth_headers

from hetdesrun.webservice.config import runtime_config
from hetdesrun.service.runtime_router import runtime_service

from hetdesrun.models.run import (
    ConfigurationInput,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)

from hetdesrun.backend.service.transformation_router import (
    nested_nodes,
    contains_deprecated,
)
from hetdesrun.backend.models.workflow import WorkflowRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto

from hetdesrun.persistence.dbservice.revision import (
    delete_single_transformation_revision,
    read_single_transformation_revision,
    store_single_transformation_revision,
    select_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
    get_all_nested_transformation_revisions,
)

from hetdesrun.persistence.dbservice.exceptions import (
    DBTypeError,
    DBBadRequestError,
    DBNotFoundError,
    DBIntegrityError,
)
from hetdesrun.persistence.models.workflow import WorkflowContent

logger = logging.getLogger(__name__)


workflow_router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Workflow not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@workflow_router.post(
    "/",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a new workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully created the workflow"}
    },
    deprecated=True,
)
async def create_workflow_revision(
    workflow_dto: WorkflowRevisionFrontendDto,
) -> WorkflowRevisionFrontendDto:
    """Store a transformation revision of type workflow in the data base.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/ instead.
    """

    logger.info(f"create a new workflow")

    transformation_revision = workflow_dto.to_transformation_revision(
        documentation=(
            "\n"
            "# New Component/Workflow\n"
            "## Description\n"
            "## Inputs\n"
            "## Outputs\n"
            "## Details\n"
            "## Examples\n"
        )
    )

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info(f"created new workflow")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto


@workflow_router.get(
    "/",
    response_model=List[WorkflowRevisionFrontendDto],
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns a list of all workflows",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully got list of workflows"}
    },
    deprecated=True,
)
async def get_all_workflow_revisions() -> List[WorkflowRevisionFrontendDto]:
    """Get all transformation revisions of type workflow from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info(f"get all workflows")

    transformation_revision_list = select_multiple_transformation_revisions(
        type=Type.WORKFLOW
    )

    logger.info(f"got all workflows")

    workflow_dto_list = [
        WorkflowRevisionFrontendDto.from_transformation_revision(tr)
        for tr in transformation_revision_list
    ]

    return workflow_dto_list


@workflow_router.get(
    "/{id}",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the workflow with the given id.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got the workflow"}},
    deprecated=True,
)
async def get_workflow_revision_by_id(
    id: UUID = Path(
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> WorkflowRevisionFrontendDto:
    """Get a single transformation revision of type workflow from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info(f"get workflow {id}")

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info(f"found workflow with id {id}")
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    if transformation_revision.type != Type.WORKFLOW:
        msg = f"DB entry for id {id} does not have type {Type.WORKFLOW}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        transformation_revision
    )
    logger.debug(workflow_dto.json())

    return workflow_dto


@workflow_router.put(
    "/{id}",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates a workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully updated the workflow"}
    },
    deprecated=True,
)
async def update_workflow_revision(
    id: UUID,
    updated_workflow_dto: WorkflowRevisionFrontendDto,
) -> WorkflowRevisionFrontendDto:
    """Update or store a transformation revision of type workflow in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info(f"update workflow {id}")

    if id != updated_workflow_dto.id:
        msg = (
            "The id {id} does not match "
            f"the id of the provided workflow revision DTO {updated_workflow_dto.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    updated_transformation_revision = updated_workflow_dto.to_transformation_revision()

    existing_operator_ids: List[UUID] = []

    try:
        existing_transformation_revision = read_single_transformation_revision(
            id, log_error=False
        )
        logger.info(f"found transformation revision {id}")

        if existing_transformation_revision.type != Type.WORKFLOW:
            msg = f"transformation revision {id} is not a workflow!"
            logger.error(msg)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

        assert isinstance(
            existing_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        updated_transformation_revision.documentation = (
            existing_transformation_revision.documentation
        )

        for operator in existing_transformation_revision.content.operators:
            existing_operator_ids.append(operator.id)

        if existing_transformation_revision.state == State.RELEASED:
            if updated_workflow_dto.state == State.DISABLED:
                logger.info(f"deprecate transformation revision {id}")
                updated_transformation_revision = existing_transformation_revision
                updated_transformation_revision.deprecate()
            else:
                msg = f"cannot modify released component {id}"
                logger.error(msg)
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)
    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the workflow revision
        pass

    for operator in updated_transformation_revision.content.operators:
        if operator.type == Type.WORKFLOW and operator.id not in existing_operator_ids:
            operator.state = (
                State.DISABLED
                if contains_deprecated(operator.transformation_id)
                else operator.state
            )

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision
            )
        )
        logger.info(f"updated workflow {id}")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto.dict(exclude_none=True, by_alias=True)


@workflow_router.delete(
    "/{id}",
    summary="Deletes a workflow.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Successfully deleted the workflow"
        },
        status.HTTP_403_FORBIDDEN: {"description": "Workflow is already released"},
    },
    deprecated=True,
)
async def delete_workflow_revision(
    id: UUID,
) -> None:
    """Delete a transformation revision of type workflow from the data base.

    Deleting a transformation revision is only possible if it is in state DRAFT.

    This endpoint is deprecated and will be removed soon,
    use DELETE /api/transformations/{id} instead.
    """

    logger.info(f"delete workflow {id}")

    try:
        delete_single_transformation_revision(id, type=Type.WORKFLOW)
        logger.info(f"deleted workflow {id}")

    except DBTypeError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))

    except DBBadRequestError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e))

    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))


@workflow_router.post(
    "/{id}/execute",
    response_model=ExecutionResponseFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Executes a new workflow.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Successfully executed the workflow"}
    },
    deprecated=True,
)
async def execute_workflow_revision(
    id: UUID,
    wiring_dto: WiringFrontendDto,
    run_pure_plot_operators: bool = False,
) -> ExecutionResponseFrontendDto:
    """Execute a transformation revision of type workflow.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/{id}/execute instead.
    """

    try:
        tr_workflow = read_single_transformation_revision(id)
        logger.info(f"found transformation revision with id {id}")
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    if tr_workflow.type != Type.WORKFLOW:
        msg = f"DB entry for id {id} does not have type {Type.WORKFLOW}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    nested_transformations = get_all_nested_transformation_revisions(tr_workflow)
    nested_components = {
        tr.id: tr for tr in nested_transformations.values() if tr.type == Type.COMPONENT
    }

    execution_input = WorkflowExecutionInput(
        code_modules=[
            tr_component.to_code_module() for tr_component in nested_components.values()
        ],
        components=[
            tr_component.to_component_revision()
            for tr_component in nested_components.values()
        ],
        workflow=tr_workflow.to_workflow_node(
            uuid4(), nested_nodes(tr_workflow, nested_transformations)
        ),
        configuration=ConfigurationInput(
            name=str(tr_workflow.id),
            run_pure_plot_operators=run_pure_plot_operators,
        ),
        workflow_wiring=wiring_dto.to_workflow_wiring(),
    )

    output_types = {
        output.name: output.type for output in execution_input.workflow.outputs
    }

    execution_result: WorkflowExecutionResult

    if runtime_config.is_runtime_service:
        execution_result = await runtime_service(execution_input)
    else:
        headers = get_auth_headers()

        async with httpx.AsyncClient(
            verify=runtime_config.hd_runtime_verify_certs
        ) as client:
            url = posix_urljoin(runtime_config.hd_runtime_engine_url, "runtime")
            try:
                response = await client.post(
                    url,
                    headers=headers,  # TODO: authentication
                    json=json.loads(
                        execution_input.json()
                    ),  # TODO: avoid double serialization. see https://github.com/samuelcolvin/pydantic/issues/1409
                    # see also https://github.com/samuelcolvin/pydantic/issues/1409#issuecomment-877175194
                )
            except httpx.HTTPError as e:
                msg = f"Failure connecting to hd runtime endpoint ({url}):\n{e}"
                logger.info(msg)
                raise HTTPException(status.HTTP_424_FAILED_DEPENDENCY, detail=msg)
            try:
                json_obj = response.json()
                execution_result = WorkflowExecutionResult(**json_obj)
            except ValidationError as e:
                msg = (
                    f"Could not validate hd runtime result object. Exception:\n{str(e)}"
                    f"\nJson Object is:\n{str(json_obj)}"
                )
                logger.info(msg)
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=msg)

    execution_response = ExecutionResponseFrontendDto(
        error=execution_result.error,
        output_results_by_output_name=execution_result.output_results_by_output_name,
        output_types_by_output_name=output_types,
        result=execution_result.result,
        traceback=execution_result.traceback,
    )

    return execution_response


@workflow_router.post(
    "/{id}/wirings",
    response_model=WorkflowRevisionFrontendDto,
    response_model_exclude_none=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Binds a wiring to the workflow.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "OK"},
        status.HTTP_204_NO_CONTENT: {"description": "Successfully bound the workflow"},
        status.HTTP_403_FORBIDDEN: {"description": "Wiring is already bound"},
    },
    deprecated=True,
)
async def bind_wiring_to_workflow_revision(
    id: UUID,
    wiring_dto: WiringFrontendDto,
) -> WiringFrontendDto:
    """Store or update the test wiring of a transformation revision of type workflow.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info(f"bind wiring to workflow {id}")

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info(f"found workflow with id {id}")
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    if transformation_revision.type != Type.WORKFLOW:
        msg = f"DB entry for id {id} does not have type {Type.WORKFLOW}"
        logger.error(msg)
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg)

    wiring = wiring_dto.to_wiring()
    transformation_revision.test_wiring = wiring

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(transformation_revision)
        )
        logger.info(f"bound wiring to workflow {id}")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

    persisted_workflow_dto = WorkflowRevisionFrontendDto.from_transformation_revision(
        persisted_transformation_revision
    )
    logger.debug(persisted_workflow_dto.json())

    return persisted_workflow_dto
