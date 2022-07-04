import datetime
import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence import Session, SQLAlchemySession
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.persistence.dbservice.exceptions import (
    DBBadRequestError,
    DBIntegrityError,
    DBNotFoundError,
)
from hetdesrun.persistence.dbservice.nesting import (
    delete_own_nestings,
    find_all_nested_transformation_revisions,
    find_all_nesting_transformation_revisions,
    update_nesting,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)


def add_tr(
    session: SQLAlchemySession, transformation_revision: TransformationRevision
) -> None:
    try:
        db_model = transformation_revision.to_orm_model()
        session.add(db_model)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store transformation revision "
            f"with id {transformation_revision.id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def store_single_transformation_revision(
    transformation_revision: TransformationRevision,
) -> None:
    with Session() as session, session.begin():

        add_tr(session, transformation_revision)

        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(
                session, transformation_revision.id, transformation_revision.content
            )


# pylint: disable=redefined-builtin
def select_tr_by_id(
    session: SQLAlchemySession, id: UUID, log_error: bool = True
) -> TransformationRevision:

    result = session.execute(
        select(TransformationRevisionDBModel).where(
            TransformationRevisionDBModel.id == id
        )
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no transformation revision in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return TransformationRevision.from_orm_model(result)


# pylint: disable=redefined-builtin
def read_single_transformation_revision(
    id: UUID, log_error: bool = True
) -> TransformationRevision:
    with Session() as session, session.begin():
        return select_tr_by_id(session, id, log_error)


def update_tr(
    session: SQLAlchemySession, transformation_revision: TransformationRevision
) -> None:
    try:
        db_model = transformation_revision.to_orm_model()
        session.execute(
            update(TransformationRevisionDBModel)
            .where(TransformationRevisionDBModel.id == db_model.id)
            .values(
                revision_group_id=db_model.revision_group_id,
                name=db_model.name,
                description=db_model.description,
                category=db_model.category,
                version_tag=db_model.version_tag,
                state=db_model.state,
                type=db_model.type,
                documentation=db_model.documentation,
                workflow_content=db_model.workflow_content,
                component_code=db_model.component_code,
                io_interface=db_model.io_interface,
                test_wiring=db_model.test_wiring,
                released_timestamp=db_model.released_timestamp,
                disabled_timestamp=db_model.disabled_timestamp,
            )
        )

    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to update "
            f"transformation revision with id {transformation_revision.id}.\n"
            f"Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def pass_on_deprecation(session: SQLAlchemySession, transformation_id: UUID) -> None:
    logger.debug(
        "pass on deprecation for transformation revision %s", str(transformation_id)
    )

    sup_nestings = find_all_nesting_transformation_revisions(session, transformation_id)

    for nesting in sup_nestings:
        transformation_revision = select_tr_by_id(session, nesting.workflow_id)
        assert isinstance(
            transformation_revision.content, WorkflowContent
        )  # hint for mypy
        for operator in transformation_revision.content.operators:
            if operator.id == nesting.via_operator_id:
                operator.state = State.DISABLED

        update_tr(session, transformation_revision)


def update_or_create_single_transformation_revision(
    transformation_revision: TransformationRevision,
) -> TransformationRevision:
    with Session() as session, session.begin():

        try:
            select_tr_by_id(session, transformation_revision.id, log_error=False)
            update_tr(session, transformation_revision)
        except DBNotFoundError:
            add_tr(session, transformation_revision)

        if transformation_revision.state == State.DISABLED:
            pass_on_deprecation(session, transformation_revision.id)

        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(
                session, transformation_revision.id, transformation_revision.content
            )

        return select_tr_by_id(session, transformation_revision.id)


# pylint: disable=redefined-builtin
def delete_single_transformation_revision(
    id: UUID, type: Optional[Type] = None
) -> None:
    with Session() as session, session.begin():

        result = select_tr_by_id(session, id)

        transformation_revision: TransformationRevision = result
        if type is not None and transformation_revision.type != type:
            msg = (
                f"Transformation revision {id} has type {transformation_revision.type}"
                f"Delete request with type {type} will not be executed"
            )
            logger.error(msg)
            raise DBBadRequestError(msg)

        if transformation_revision.state != State.DRAFT:
            msg = (
                f"Transformation revision {id} cannot be deleted "
                f"since it is in the state {transformation_revision.state}"
            )
            logger.error(msg)
            raise DBBadRequestError(msg)

        delete_own_nestings(session, transformation_revision.id)

        session.execute(
            delete(TransformationRevisionDBModel).where(
                TransformationRevisionDBModel.id == transformation_revision.id
            )
        )


# pylint: disable=redefined-builtin
def select_multiple_transformation_revisions(
    category: Optional[str] = None,
    revision_group_id: Optional[UUID] = None,
    type: Optional[Type] = None,
    state: Optional[State] = None,
) -> List[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""
    with Session() as session, session.begin():
        selection = select(TransformationRevisionDBModel)

        if category is not None:
            selection = selection.where(
                TransformationRevisionDBModel.category == category
            )
        if revision_group_id is not None:
            selection = selection.where(
                TransformationRevisionDBModel.revision_group_id == revision_group_id
            )
        if type is not None:
            selection = selection.where(TransformationRevisionDBModel.type == type)
        if state is not None:
            selection = selection.where(TransformationRevisionDBModel.state == state)

        results = session.execute(selection).scalars().all()

        return [TransformationRevision.from_orm_model(result) for result in results]


def get_all_nested_transformation_revisions(
    transformation_revision: TransformationRevision,
) -> Dict[UUID, TransformationRevision]:

    if transformation_revision.type != Type.WORKFLOW:
        msg = (
            f"cannot get operators of transformation revision {transformation_revision.id} "
            f"because its type is not WORKFLOW"
        )
        logger.error(msg)
        raise DBBadRequestError(msg)

    with Session() as session, session.begin():
        descendants = find_all_nested_transformation_revisions(
            session, transformation_revision.id
        )

    nested_transformation_revisions: Dict[UUID, TransformationRevision] = {}

    for descendant in descendants:
        nested_transformation_revisions[descendant.operator_id] = select_tr_by_id(
            session, descendant.transformation_id
        )

    return nested_transformation_revisions


def get_latest_revision_id(revision_group_id: UUID) -> UUID:
    revision_group_list = select_multiple_transformation_revisions(
        state=State.RELEASED, revision_group_id=revision_group_id
    )
    if len(revision_group_list) == 0:
        msg = (
            f"no released transformation revisions with revision group id {revision_group_id} "
            f"found in the database"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    id_by_released_timestamp: Dict[datetime.datetime, UUID] = {}

    for revision in revision_group_list:
        assert isinstance(revision.released_timestamp, datetime.datetime)
        id_by_released_timestamp[revision.released_timestamp] = revision.id
    _, latest_revision_id = sorted(id_by_released_timestamp.items(), reverse=True)[0]
    return latest_revision_id
