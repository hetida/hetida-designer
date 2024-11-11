import datetime
import logging
from copy import deepcopy
from uuid import UUID

from pydantic import StrictInt, StrictStr
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from hetdesrun.component.code import update_code
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence import SQLAlchemySession, get_session
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
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
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type, cache_conditionally

logger = logging.getLogger(__name__)


def add_tr(session: SQLAlchemySession, transformation_revision: TransformationRevision) -> None:
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
    with get_session()() as session, session.begin():
        add_tr(session, transformation_revision)

        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(  # noqa: S101
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(session, transformation_revision.id, transformation_revision.content)


def select_tr_by_id(
    session: SQLAlchemySession,
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> TransformationRevision:
    result = session.execute(
        select(TransformationRevisionDBModel).where(TransformationRevisionDBModel.id == id)
    ).scalar_one_or_none()

    if result is None:
        msg = f"Found no transformation revision in database with id {id}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)

    return TransformationRevision.from_orm_model(result)


def read_single_transformation_revision(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> TransformationRevision:
    with get_session()() as session, session.begin():
        return select_tr_by_id(session, id, log_error)


@cache_conditionally(lambda trafo: trafo.state != State.DRAFT)
def read_single_transformation_revision_with_caching(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> TransformationRevision:
    return read_single_transformation_revision(id, log_error)


def update_tr(session: SQLAlchemySession, transformation_revision: TransformationRevision) -> None:
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
                release_wiring=db_model.release_wiring,
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
    logger.debug("pass on deprecation for transformation revision %s", str(transformation_id))

    sup_nestings = find_all_nestings(session, transformation_id)

    for nesting in sup_nestings:
        transformation_revision = select_tr_by_id(session, nesting.workflow_id)
        assert isinstance(  # noqa: S101
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
) -> tuple[bool, str]:
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

    if existing_transformation_revision.state == State.DISABLED and not allow_overwrite_released:
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


def contains_deprecated(transformation_id: UUID) -> bool:
    logger.debug(
        "check if transformation revision %s contains deprecated operators",
        str(transformation_id),
    )
    transformation_revision = read_single_transformation_revision(transformation_id)

    if transformation_revision.type is not Type.WORKFLOW:
        msg = f"transformation revision {transformation_id} is not a workflow!"
        logger.error(msg)
        raise DBIntegrityError(msg)

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


def update_content(
    updated_transformation_revision: TransformationRevision,
    existing_transformation_revision: TransformationRevision | None = None,
) -> TransformationRevision:
    if updated_transformation_revision.type == Type.COMPONENT:
        updated_transformation_revision.content = update_code(updated_transformation_revision)
    elif existing_transformation_revision is not None:
        assert isinstance(  # noqa: S101
            existing_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        existing_operator_ids: list[UUID] = []
        for operator in existing_transformation_revision.content.operators:
            existing_operator_ids.append(operator.id)

        assert isinstance(  # noqa: S101
            updated_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        for operator in updated_transformation_revision.content.operators:
            if operator.type == Type.WORKFLOW and operator.id not in existing_operator_ids:
                operator.state = (
                    State.DISABLED
                    if contains_deprecated(operator.transformation_id)
                    else operator.state
                )
    return updated_transformation_revision


def if_applicable_release_or_deprecate(
    existing_transformation_revision: TransformationRevision | None,
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
            updated_transformation_revision.content = existing_transformation_revision.content
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
            updated_transformation_revision.content = existing_transformation_revision.content
    return updated_transformation_revision


def update_or_create_single_transformation_revision(
    transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = False,
    update_component_code: bool = True,
    strip_wiring: bool = False,
    strip_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
    keep_only_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
    strip_release_wiring: bool = False,
    strip_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
    keep_only_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
) -> TransformationRevision:
    transformation_revision.strip_wirings(
        strip_wiring=strip_wiring,
        strip_wirings_with_adapter_ids=strip_wirings_with_adapter_ids,
        keep_only_wirings_with_adapter_ids=keep_only_wirings_with_adapter_ids,
        strip_release_wiring=strip_release_wiring,
        strip_release_wirings_with_adapter_ids=strip_release_wirings_with_adapter_ids,
        keep_only_release_wirings_with_adapter_ids=keep_only_release_wirings_with_adapter_ids,
    )

    with get_session()() as session, session.begin():
        try:
            existing_transformation_revision = select_tr_by_id(
                session, transformation_revision.id, log_error=False
            )
        except DBNotFoundError:
            if transformation_revision.type == Type.WORKFLOW or update_component_code:
                transformation_revision = update_content(transformation_revision)

            add_tr(session, transformation_revision)
        else:
            modifiable, msg = is_modifiable(
                existing_transformation_revision=existing_transformation_revision,
                updated_transformation_revision=transformation_revision,
                allow_overwrite_released=allow_overwrite_released,
            )

            if modifiable is False:
                raise ModifyForbidden(msg)

            transformation_revision = if_applicable_release_or_deprecate(
                existing_transformation_revision, transformation_revision
            )

            if transformation_revision.type == Type.WORKFLOW or update_component_code:
                transformation_revision = update_content(
                    transformation_revision, existing_transformation_revision
                )

            update_tr(session, transformation_revision)

        if transformation_revision.state == State.DISABLED:
            pass_on_deprecation(session, transformation_revision.id)
            return select_tr_by_id(session, transformation_revision.id)

        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(  # noqa: S101
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(session, transformation_revision.id, transformation_revision.content)

        return select_tr_by_id(session, transformation_revision.id)


def delete_tr(session: SQLAlchemySession, tr_id: UUID) -> None:
    try:
        session.execute(
            delete(TransformationRevisionDBModel).where(TransformationRevisionDBModel.id == tr_id)
        )
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to delete transformation revision "
            f"with id {tr_id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def delete_single_transformation_revision(
    id: UUID,  # noqa: A002
    type: Type | None = None,  # noqa: A002
    ignore_state: bool = False,
) -> None:
    with get_session()() as session, session.begin():
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

    with get_session()() as session, session.begin():
        sup_nestings = find_all_nestings(session, transformation_id)

        containing_wf_ids = [nesting.workflow_id for nesting in sup_nestings]

        selection = (
            select(TransformationRevisionDBModel)
            .where(TransformationRevisionDBModel.id.in_(containing_wf_ids))
            .where(TransformationRevisionDBModel.state != State.DISABLED)
        )

    results = session.execute(selection).scalars().all()
    return len(results) == 0


def select_multiple_transformation_revisions(
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    revision_group_id: UUID | None = None,
    ids: list[UUID] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
) -> list[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""
    with get_session()() as session, session.begin():
        selection = select(TransformationRevisionDBModel)

        if type is not None:
            selection = selection.where(TransformationRevisionDBModel.type == type)
        if state is not None:
            selection = selection.where(TransformationRevisionDBModel.state == state)
        if categories is not None:
            selection = selection.where(TransformationRevisionDBModel.category.in_(categories))
        if category_prefix is not None:
            selection = selection.where(
                TransformationRevisionDBModel.category.startswith(category_prefix, autoescape=True)
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
            selection = selection.where(TransformationRevisionDBModel.state != State.DISABLED)

        results = session.execute(selection).scalars().all()

        tr_list = [TransformationRevision.from_orm_model(result) for result in results]

        return tr_list


def get_multiple_transformation_revisions(
    params: FilterParams,
) -> list[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""
    tr_list = select_multiple_transformation_revisions(
        type=params.type,
        state=params.state,
        categories=params.categories,
        category_prefix=params.category_prefix,
        revision_group_id=params.revision_group_id,
        ids=params.ids,
        names=params.names,
        include_deprecated=params.include_deprecated,
    )

    if params.unused:
        tr_list = [tr for tr in tr_list if is_unused(tr.id)]

    if params.include_dependencies:
        dependencies = []
        tr_ids = {tr.id for tr in tr_list}
        for tr in tr_list:
            if tr.type == Type.WORKFLOW:
                nested_tr_dict = get_all_nested_transformation_revisions(tr)
                for nested_tr_id in nested_tr_dict:
                    if nested_tr_id not in tr_ids:
                        tr_ids.add(nested_tr_id)
                        dependencies.append(nested_tr_dict[nested_tr_id])
        tr_list = tr_list + dependencies

    return tr_list


def nof_db_entries() -> int:
    with get_session()() as session, session.begin():
        nof_rows: int = session.query(TransformationRevisionDBModel.id).count()
        logger.info("DB contains %s rows", str(nof_rows))

    return nof_rows


def get_all_nested_transformation_revisions(
    transformation_revision: TransformationRevision,
) -> dict[UUID, TransformationRevision]:
    if transformation_revision.type != Type.WORKFLOW:
        msg = (
            f"cannot get operators of transformation revision {transformation_revision.id} "
            f"because its type is not WORKFLOW"
        )
        logger.error(msg)
        raise TypeConflict(msg)

    with get_session()() as session, session.begin():
        descendants = find_all_nested_transformation_revisions(session, transformation_revision.id)

        nested_transformation_revisions: dict[UUID, TransformationRevision] = {}

        for descendant in descendants:
            nested_transformation_revisions[descendant.operator_id] = select_tr_by_id(
                session, descendant.transformation_id
            )

    return nested_transformation_revisions


def get_latest_revision_id(revision_group_id: UUID) -> UUID:
    revision_group_list = get_multiple_transformation_revisions(
        FilterParams(
            state=State.RELEASED,
            revision_group_id=revision_group_id,
            include_dependencies=False,
        )
    )
    if len(revision_group_list) == 0:
        msg = (
            f"no released transformation revisions with revision group id {revision_group_id} "
            f"found in the database"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    id_by_released_timestamp: dict[datetime.datetime, UUID] = {}

    for revision in revision_group_list:
        if not isinstance(revision.released_timestamp, datetime.datetime):
            raise TypeError("revision.released_timestamp must be of type datetime.datetime")
        id_by_released_timestamp[revision.released_timestamp] = revision.id
    _, latest_revision_id = sorted(id_by_released_timestamp.items(), reverse=True)[0]
    return latest_revision_id
