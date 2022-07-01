from typing import List
import logging

from uuid import UUID

from fastapi import APIRouter, Path, status, HTTPException

from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto

from hetdesrun.utils import Type, State

from hetdesrun.persistence.dbservice.revision import (
    read_single_transformation_revision,
    store_single_transformation_revision,
    select_multiple_transformation_revisions,
    update_or_create_single_transformation_revision,
)

from hetdesrun.persistence.dbservice.exceptions import DBNotFoundError, DBIntegrityError

from hetdesrun.backend.service.component_router import generate_code

logger = logging.getLogger(__name__)


base_item_router = APIRouter(
    prefix="/base-items",
    tags=["base items"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Forbidden"},
        status.HTTP_404_NOT_FOUND: {"description": "Not Found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@base_item_router.get(
    "/",
    response_model=List[TransformationRevisionFrontendDto],
    response_model_exclude_unset=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns combined list of all base items (components and workflows)",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got all base items"}},
    deprecated=True,
)
async def get_all_transformation_revisions() -> List[TransformationRevisionFrontendDto]:
    """Get all transformation revisions without their content from the data base.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/ instead
    """

    logger.info("get all transformation revisions")

    try:
        transformation_revision_list = select_multiple_transformation_revisions()
    except DBIntegrityError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"At least one entry in the DB is no valid transformation revision:\n{str(e)}",
        ) from e

    transformation_revision_dto_list = [
        TransformationRevisionFrontendDto.from_transformation_revision(tr)
        for tr in transformation_revision_list
    ]

    return transformation_revision_dto_list


@base_item_router.get(
    "/{id}",
    response_model=TransformationRevisionFrontendDto,
    response_model_exclude_unset=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Returns the base item with the given id.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_200_OK: {"description": "Successfully got the base item"}},
    deprecated=True,
)
async def get_transformation_revision_by_id(
    # pylint: disable=redefined-builtin
    id: UUID = Path(
        ...,
        example=UUID("123e4567-e89b-12d3-a456-426614174000"),
    ),
) -> TransformationRevisionFrontendDto:
    """Get a single transformation revision without its content from the data base by its id.

    This endpoint is deprecated and will be removed soon,
    use GET /api/transformations/{id} instead.
    """

    logger.info("get base item %s", id)

    try:
        transformation_revision = read_single_transformation_revision(id)
        logger.info("found transformation revision with id %s", id)
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    transformation_revision_dto = (
        TransformationRevisionFrontendDto.from_transformation_revision(
            transformation_revision
        )
    )
    logger.debug(transformation_revision_dto.json())

    return transformation_revision_dto


@base_item_router.post(
    "/",
    response_model=TransformationRevisionFrontendDto,
    response_model_exclude_unset=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Creates a new item.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully created the item"}
    },
    deprecated=True,
)
async def create_transformation_revision(
    transformation_revision_dto: TransformationRevisionFrontendDto,
) -> TransformationRevisionFrontendDto:
    """Store a transformation revision without content in the data base.

    This endpoint is deprecated and will be removed soon,
    use POST /api/transformations/ instead.
    """

    logger.info("create base item %s", transformation_revision_dto.id)

    transformation_revision = transformation_revision_dto.to_transformation_revision(
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

    if transformation_revision.type == Type.COMPONENT:
        logger.debug("transformation revision has type %s", Type.COMPONENT)
        transformation_revision.content = generate_code(
            transformation_revision.to_code_body()
        )
        logger.debug("generated code:\n%s", transformation_revision.content)

    try:
        store_single_transformation_revision(transformation_revision)
        logger.info("created base item")
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    try:
        persisted_transformation_revision = read_single_transformation_revision(
            transformation_revision.id
        )
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    persisted_transformation_dto = (
        TransformationRevisionFrontendDto.from_transformation_revision(
            persisted_transformation_revision
        )
    )
    logger.debug(persisted_transformation_dto.json())

    return persisted_transformation_dto


@base_item_router.put(
    "/{id}",
    response_model=TransformationRevisionFrontendDto,
    response_model_exclude_unset=True,  # needed because:
    # frontend handles attributes with value null in a different way than missing attributes
    summary="Updates basic attributes of a component or workflow.",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Successfully updated the item"}
    },
    deprecated=True,
)
async def update_transformation_revision(
    # pylint: disable=redefined-builtin
    id: UUID,
    updated_transformation_revision_dto: TransformationRevisionFrontendDto,
) -> TransformationRevisionFrontendDto:
    """Update or store a transformation revision except for its content in the data base.

    If no DB entry with the provided id is found, it will be created.

    Updating a transformation revision is only possible if it is in state DRAFT
    or to change the state from RELEASED to DISABLED.

    This endpoint is deprecated and will be removed soon,
    use PUT /api/transformations/{id} instead.
    """

    logger.info("update base item %s", id)

    if id != updated_transformation_revision_dto.id:
        msg = (
            f"The id {id} does not match "
            f"the id of the provided base item DTO {updated_transformation_revision_dto.id}"
        )
        logger.error(msg)
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

    updated_transformation_revision = (
        updated_transformation_revision_dto.to_transformation_revision()
    )

    try:
        existing_transformation_revision = read_single_transformation_revision(id)

        if (
            existing_transformation_revision.type
            != updated_transformation_revision_dto.type
        ):
            msg = (
                f"The type ({updated_transformation_revision_dto.type}) "
                f"of the provided transformation revision does not\n"
                f"match the type ({existing_transformation_revision.type}) "
                f"of the stored transformation revision {id}!"
            )
            logger.error(msg)
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)

        updated_transformation_revision.content = (
            existing_transformation_revision.content
        )
        if existing_transformation_revision.type == Type.COMPONENT:
            updated_transformation_revision.content = (
                updated_transformation_revision.content
            ) = generate_code(updated_transformation_revision.to_code_body())
        updated_transformation_revision.documentation = (
            existing_transformation_revision.documentation
        )

        if existing_transformation_revision.state == State.RELEASED:
            if updated_transformation_revision_dto.state == State.DISABLED:
                logger.info("deprecate transformation revision %s", id)
                updated_transformation_revision = existing_transformation_revision
                updated_transformation_revision.deprecate()
            else:
                msg = f"cannot modify released component {id}"
                logger.error(msg)
                raise HTTPException(status.HTTP_403_FORBIDDEN, detail=msg)
    except DBNotFoundError:
        # base/example workflow deployment needs to be able to put
        # with an id and either create or update the component revision
        pass

    try:
        persisted_transformation_revision = (
            update_or_create_single_transformation_revision(
                updated_transformation_revision
            )
        )
        logger.info("updated base item %s", id)
    except DBIntegrityError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
    except DBNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    persisted_transformation_dto = (
        TransformationRevisionFrontendDto.from_transformation_revision(
            persisted_transformation_revision
        )
    )
    logger.debug(persisted_transformation_dto.json())

    return persisted_transformation_dto
