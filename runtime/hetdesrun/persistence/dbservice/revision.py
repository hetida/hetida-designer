import datetime
import logging
from copy import deepcopy
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence import Session, SQLAlchemySession
from hetdesrun.persistence.dbmodels import FilterParams, TransformationRevisionDBModel
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNotFoundError
from hetdesrun.persistence.dbservice.nesting import (
    delete_own_nestings,
    find_all_nested_transformation_revisions,
    find_all_nestings,
    update_nesting,
)
from hetdesrun.persistence.models.exceptions import (
    ModifyForbidden,
    StateConflict,
    TypeConflict,
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

    sup_nestings = find_all_nestings(session, transformation_id)

    for nesting in sup_nestings:
        transformation_revision = select_tr_by_id(session, nesting.workflow_id)
        assert isinstance(
            transformation_revision.content, WorkflowContent
        )  # hint for mypy
        for operator in transformation_revision.content.operators:
            if operator.id == nesting.via_operator_id:
                operator.state = State.DISABLED

        update_tr(session, transformation_revision)


def tr_same_except_for_wiring_and_docu(
    tr_A: TransformationRevision, tr_B: TransformationRevision
) -> bool:
    tr_compare = deepcopy(tr_A)
    tr_compare.test_wiring = tr_B.test_wiring
    tr_compare.documentation = tr_B.documentation
    are_equal = tr_compare == tr_B
    return are_equal


def is_modifiable(
    existing_transformation_revision: TransformationRevision,
    updated_transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = False,
) -> Tuple[bool, str]:
    if existing_transformation_revision.type != updated_transformation_revision.type:
        return False, (
            f"The type ({updated_transformation_revision.type}) of the "
            f"provided transformation revision does not\n"
            f"match the type ({existing_transformation_revision.type}) "
            f"of the stored transformation revision {existing_transformation_revision.id}!"
        )

    if tr_same_except_for_wiring_and_docu(
        existing_transformation_revision, updated_transformation_revision
    ):
        return True, ""

    if (
        existing_transformation_revision.state == State.DISABLED
        and not allow_overwrite_released
    ):
        return False, (
            f"Cannot modify deprecated transformation revision "
            f"{existing_transformation_revision.id}!"
        )

    if (
        existing_transformation_revision.state == State.RELEASED
        and updated_transformation_revision.state != State.DISABLED
        and not allow_overwrite_released
    ):
        return False, (
            f"Cannot modify released transformation revision "
            f"{existing_transformation_revision.id}!"
        )

    return True, ""


def update_or_create_single_transformation_revision(
    transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = False,
) -> TransformationRevision:
    with Session() as session, session.begin():

        try:
            existing_transformation_revision = select_tr_by_id(
                session, transformation_revision.id, log_error=False
            )
        except DBNotFoundError:
            add_tr(session, transformation_revision)
        else:
            modifiable, msg = is_modifiable(
                existing_transformation_revision=existing_transformation_revision,
                updated_transformation_revision=transformation_revision,
                allow_overwrite_released=allow_overwrite_released,
            )

            if modifiable is False:
                raise ModifyForbidden(msg)

            update_tr(session, transformation_revision)

        if transformation_revision.state == State.DISABLED:
            pass_on_deprecation(session, transformation_revision.id)
            return select_tr_by_id(session, transformation_revision.id)

        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(
                session, transformation_revision.id, transformation_revision.content
            )

        return select_tr_by_id(session, transformation_revision.id)


def delete_tr(session: SQLAlchemySession, tr_id: UUID) -> None:
    try:
        session.execute(
            delete(TransformationRevisionDBModel).where(
                TransformationRevisionDBModel.id == tr_id
            )
        )
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to delete transformation revision "
            f"with id {tr_id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


# pylint: disable=redefined-builtin
def delete_single_transformation_revision(
    id: UUID, type: Optional[Type] = None, ignore_state: bool = False
) -> None:
    with Session() as session, session.begin():

        result = select_tr_by_id(session, id)

        transformation_revision: TransformationRevision = result
        if type is not None and transformation_revision.type != type:
            msg = (
                f"Transformation revision {id} has type {transformation_revision.type}, "
                f"delete request with type {type} will not be executed"
            )
            logger.error(msg)
            raise TypeConflict(msg)

        if not ignore_state and transformation_revision.state != State.DRAFT:
            msg = (
                f"Transformation revision {id} cannot be deleted "
                f"since it is in the state {transformation_revision.state}"
            )
            logger.error(msg)
            raise StateConflict(msg)

        delete_own_nestings(session, transformation_revision.id)

        delete_tr(session, transformation_revision.id)


def is_unused(transformation_id: UUID) -> bool:
    """Determine if transformation revision is unused.

    More precisely: Determine if specified transformation revision is only contained in
    transformation revisions which are deprecated, i.e. have the state DISABLED.
    """

    with Session() as session, session.begin():
        sup_nestings = find_all_nestings(session, transformation_id)

        containing_wf_ids = [nesting.workflow_id for nesting in sup_nestings]

        selection = (
            select(TransformationRevisionDBModel)
            .where(TransformationRevisionDBModel.id.in_(containing_wf_ids))
            .where(TransformationRevisionDBModel.state != State.DISABLED)
        )

    results = session.execute(selection).scalars().all()
    if len(results) == 0:
        return True

    return False


def select_multiple_transformation_revisions(
    type: Optional[Type] = None,  # pylint: disable=redefined-builtin
    state: Optional[State] = None,
    categories: Optional[List[ValidStr]] = None,
    revision_group_id: Optional[UUID] = None,
    ids: Optional[List[UUID]] = None,
    names: Optional[List[NonEmptyValidStr]] = None,
    include_deprecated: bool = True,
) -> List[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""
    with Session() as session, session.begin():
        selection = select(TransformationRevisionDBModel)

        if type is not None:
            selection = selection.where(TransformationRevisionDBModel.type == type)
        if state is not None:
            selection = selection.where(TransformationRevisionDBModel.state == state)
        if categories is not None:
            selection = selection.where(
                TransformationRevisionDBModel.category.in_(categories)
            )
        if revision_group_id is not None:
            selection = selection.where(
                TransformationRevisionDBModel.revision_group_id == revision_group_id
            )
        if ids is not None:
            selection = selection.where(TransformationRevisionDBModel.id.in_(ids))
        if names is not None:
            selection = selection.where(
                TransformationRevisionDBModel.name.in_(names),
            )
        if not include_deprecated:
            selection = selection.where(
                TransformationRevisionDBModel.state != State.DISABLED
            )

        results = session.execute(selection).scalars().all()

        tr_list = [TransformationRevision.from_orm_model(result) for result in results]

        return tr_list


def get_all_categories() -> List[ValidStr]:
    pass


def get_categories_with_prefix(prefix: ValidStr) -> List[ValidStr]:
    categories = get_all_categories()
    return [category for category in categories if str(category).startwith(prefix)]


def get_multiple_transformation_revisions(
    params: FilterParams,
) -> List[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""
    categories = params.categories
    if params.categories_with_prefix is not None:
        categories_with_prefix = get_categories_with_prefix(
            params.categories_with_prefix
        )
        categories = categories + categories_with_prefix

    tr_list = select_multiple_transformation_revisions(
        type=params.type,
        state=params.state,
        categories=params.categories,
        revision_group_id=params.revision_group_id,
        ids=params.ids,
        names=params.names,
        include_deprecated=params.include_deprecated,
    )

    if params.unused:
        tr_list = [tr for tr in tr_list if is_unused(tr.id)]

    if params.include_dependencies:
        tr_ids = [tr.id for tr in tr_list]
        for tr in tr_list:
            if tr.type == Type.WORKFLOW:
                nested_tr_dict = get_all_nested_transformation_revisions(tr)
                for (
                    nested_tr_id
                ) in nested_tr_dict:  # pylint: disable=consider-using-dict-items
                    if nested_tr_id not in tr_ids:
                        tr_list.append(nested_tr_dict[nested_tr_id])

    return tr_list


def nof_db_entries() -> int:
    with Session() as session, session.begin():
        nof_rows = session.query(TransformationRevisionDBModel.id).count()
        logger.info("DB contains %s rows", str(nof_rows))

    return nof_rows


def get_all_nested_transformation_revisions(
    transformation_revision: TransformationRevision,
) -> Dict[UUID, TransformationRevision]:

    if transformation_revision.type != Type.WORKFLOW:
        msg = (
            f"cannot get operators of transformation revision {transformation_revision.id} "
            f"because its type is not WORKFLOW"
        )
        logger.error(msg)
        raise TypeConflict(msg)

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
    revision_group_list = get_multiple_transformation_revisions(
        FilterParams(state=State.RELEASED, revision_group_id=revision_group_id)
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
