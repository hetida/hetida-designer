import logging
from uuid import UUID

from pydantic import StrictInt, StrictStr
from sqlalchemy import delete, distinct, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import load_only
from sqlalchemy.sql.selectable import Select

from hetdesrun.component.code import expand_code, update_code
from hetdesrun.component.code_utils import CodeParsingException, get_global_component_imports
from hetdesrun.models.code import NonEmptyValidStr, ValidStr
from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.dbmodels import NestingDBModel, TransformationRevisionDBModel
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
from hetdesrun.persistence.models.transformation import (
    TransformationRevision,
    TransformationRevisionStub,
)
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.filter.params import FilterParams
from hetdesrun.utils import State, Type, cache_conditionally, cache_output_dict_conditionally
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def add_tr(session: SQLAlchemySession, transformation_revision: TransformationRevision) -> None:
    try:
        db_model = transformation_revision.to_orm_model()
        session.add(db_model)
        # Flush here so that a constraint violation (e.g. a duplicate id from a concurrent
        # create) surfaces as an IntegrityError at this point and is mapped to
        # DBIntegrityError. session.add() alone only stages the row; without the flush the
        # error would first be raised at the surrounding transaction's commit, where it
        # escapes unmapped as a raw sqlalchemy IntegrityError (HTTP 500).
        session.flush()
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


@cache_conditionally(
    lambda trafo: (
        get_config().enable_caching_for_non_draft_trafos_for_execution
        and trafo.state != State.DRAFT
    )
)
def select_tr_by_id_with_possible_caching(
    id: UUID,  # noqa: A002
    session: SQLAlchemySession,
    log_error: bool = True,
) -> TransformationRevision:
    """Like select_tr_by_id, but caches non-DRAFT trafos when the flag is enabled.

    Caching is opt-in (enable_caching_for_non_draft_trafos_for_execution) and only kicks in
    for non-DRAFT (i.e. immutable) revisions. On a cache hit the SAME object is returned, so
    callers MUST NOT mutate the result in place. See cache_conditionally for the full
    contract (shared objects, unbounded, no invalidation).
    """
    return select_tr_by_id(session=session, id=id, log_error=log_error)


def read_multiple_transformation_revisions_by_id(
    ids: tuple[UUID, ...], log_error: bool = True, session: SQLAlchemySession | None = None
) -> dict[UUID, TransformationRevision]:
    if not ids:
        return {}

    # normalize to UUID: callers pass either UUIDs (nested descendants) or uuid strings
    # (parsed component imports), and the missing-id check below must compare like types.
    requested_ids = [UUID(str(id_)) for id_ in ids]
    # single IN query instead of one SELECT per id (avoids N+1 on the execution path)
    selection = multiple_trafo_select_filtered(ids=requested_ids)

    # the orm results must be converted while the session is still open, so build the
    # dict inside the session scope
    if session is None:
        with get_session()() as new_session, new_session.begin():
            results = new_session.execute(selection).scalars().all()
            trafos_by_id = {tr.id: tr for tr in map(TransformationRevision.from_orm_model, results)}
    else:
        results = session.execute(selection).scalars().all()
        trafos_by_id = {tr.id: tr for tr in map(TransformationRevision.from_orm_model, results)}

    # preserve the previous contract: raise if any requested id is missing
    missing_ids = set(requested_ids) - set(trafos_by_id)
    if missing_ids:
        msg = f"Found no transformation revision in database for ids {missing_ids}"
        if log_error:
            logger.error(msg)
        raise DBNotFoundError(msg)
    return trafos_by_id


@cache_output_dict_conditionally(
    lambda trafo: (
        get_config().enable_caching_for_non_draft_trafos_for_execution
        and trafo.state != State.DRAFT
    )
)
def read_multiple_transformation_revisions_by_id_with_possible_caching(
    ids: tuple[UUID, ...], log_error: bool = True, session: SQLAlchemySession | None = None
) -> dict[UUID, TransformationRevision]:
    """Like read_multiple_transformation_revisions_by_id, but caches non-DRAFT trafos.

    Caching is opt-in (enable_caching_for_non_draft_trafos_for_execution) and only kicks in
    for non-DRAFT (i.e. immutable) revisions. Cached values are shared objects, so callers
    MUST NOT mutate them in place. See cache_output_dict_conditionally for the full contract
    (shared values, unbounded, no invalidation).
    """
    return read_multiple_transformation_revisions_by_id(ids, log_error=log_error, session=session)


def read_single_transformation_revision(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> TransformationRevision:
    with get_session()() as session, session.begin():
        return select_tr_by_id(session, id, log_error)


@cache_conditionally(
    lambda trafo: (
        get_config().enable_caching_for_non_draft_trafos_for_execution
        and trafo.state != State.DRAFT
    )
)
def read_single_transformation_revision_with_caching(
    id: UUID,  # noqa: A002
    log_error: bool = True,
) -> TransformationRevision:
    """Like read_single_transformation_revision, but caches non-DRAFT trafos.

    Caching is opt-in (enable_caching_for_non_draft_trafos_for_execution) and only kicks in
    for non-DRAFT (i.e. immutable) revisions. On a cache hit the SAME object is returned, so
    callers MUST NOT mutate the result in place. See cache_conditionally for the full
    contract (shared objects, unbounded, no invalidation).
    """
    return read_single_transformation_revision(id, log_error)


def recursively_load_with_component_imports(
    current_ids: tuple[UUID, ...],
    already_fetched_dict: dict[UUID, TransformationRevision],
    current_session: SQLAlchemySession,
    log_error: bool = True,
    possibly_caching: bool = True,
) -> dict[UUID, TransformationRevision]:
    current_level_trafo_dict = {
        trafo_id: (
            select_tr_by_id_with_possible_caching(trafo_id, current_session, log_error=log_error)
            if possibly_caching
            else select_tr_by_id(current_session, trafo_id, log_error=log_error)
        )
        for trafo_id in current_ids
        if not trafo_id in already_fetched_dict
    }

    for trafo_id, trafo in current_level_trafo_dict.items():
        already_fetched_dict[trafo_id] = trafo

    newly_added_components = {
        trafo_id: trafo
        for trafo_id, trafo in current_level_trafo_dict.items()
        if trafo.type is Type.COMPONENT
    }

    direct_imports = []
    for trafo in newly_added_components.values():
        assert isinstance(trafo.content, str)  # noqa: S101 # for mypy
        direct_import_ids = get_global_component_imports(trafo.content)
        direct_imports.extend(direct_import_ids)

    if len(direct_imports) > 0:
        recursively_load_with_component_imports(
            tuple(comp_id for comp_id in direct_imports if not comp_id in already_fetched_dict),
            already_fetched_dict,
            current_session,
            log_error,
        )

    return already_fetched_dict


def read_component_imports_recursively(
    trafos: list[TransformationRevision],
    log_error: bool = True,
    session: SQLAlchemySession | None = None,
    possibly_caching: bool = True,
) -> dict[UUID, TransformationRevision]:
    """Obtains all components imported by the given components

    trafos can be arbitrary TransformationRevision objects, however, workflows will
    be ignored. Of all components given, this loads components imported by them recursively,
    ignoring (and not loading) the initial components, even if they occur at
    some recursion level.

    Returns the loaded components only (and not the initial components).
    """

    initial_components_dict = {trafo.id: trafo for trafo in trafos if trafo.type is Type.COMPONENT}
    initial_component_ids = set(initial_components_dict.keys())

    all_direct_import_ids = set()

    for component in initial_components_dict.values():
        if component.type is Type.COMPONENT:
            assert isinstance(component.content, str)  # noqa: S101 # for mypy
            direct_import_ids = get_global_component_imports(component.content)
            all_direct_import_ids.update(direct_import_ids)

    if session is None:
        with get_session()() as new_session, new_session.begin():
            loaded_component_imports_dict = recursively_load_with_component_imports(
                tuple(all_direct_import_ids),
                initial_components_dict,  # this will be mutated!
                new_session,
                log_error=log_error,
                possibly_caching=possibly_caching,
            )

    else:
        loaded_component_imports_dict = recursively_load_with_component_imports(
            tuple(all_direct_import_ids),
            initial_components_dict,  # this will be mutated!
            session,
            log_error=log_error,
            possibly_caching=possibly_caching,
        )

    return {
        tr_id: tr
        for tr_id, tr in loaded_component_imports_dict.items()
        if not tr_id in initial_component_ids
    }


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
    # Shallow copy instead of deepcopy: we only override two fields and compare, never
    # mutating the shared nested content, so there is no need to duplicate the
    # (potentially large) workflow content.
    tr_compare = tr_A.model_copy(
        update={"test_wiring": tr_B.test_wiring, "documentation": tr_B.documentation}
    )
    return tr_compare == tr_B


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
            f"Cannot modify released transformation revision {existing_transformation_revision.id}!"
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
    found_some_disabled: bool = False
    for operator in transformation_revision.content.operators:
        if operator.state is State.DISABLED:
            logger.debug(
                "operator with transformation id %s has status %s",
                str(operator.transformation_id),
                operator.state,
            )
            found_some_disabled = True

    return found_some_disabled


def refresh_deprecated_operator_states(
    session: SQLAlchemySession, workflow_content: WorkflowContent
) -> None:
    """Flag operators that reference a deprecated (DISABLED) transformation.

    operator.state is a denormalized snapshot of the referenced transformation's state
    (used e.g. by the frontend to indicate operators whose transformation is deprecated).
    It can be stale in incoming content -- most notably when importing a workflow whose
    referenced transformation was already deprecated, so that pass_on_deprecation never
    reached this workflow. Recompute the DISABLED flag from the db.

    This uses a single query projecting only the ids of the referenced transformations
    that are deprecated (no full transformation contents are loaded), so it stays cheap
    even though workflows are stored on every edit.
    """
    operators = workflow_content.operators
    if not operators:
        return

    referenced_ids = {operator.transformation_id for operator in operators}
    disabled_ids = set(
        session.execute(
            select(TransformationRevisionDBModel.id).where(
                TransformationRevisionDBModel.id.in_(referenced_ids),
                TransformationRevisionDBModel.state == State.DISABLED,
            )
        )
        .scalars()
        .all()
    )

    for operator in operators:
        if operator.transformation_id in disabled_ids:
            operator.state = State.DISABLED


def update_content(
    updated_transformation_revision: TransformationRevision,
    existing_transformation_revision: TransformationRevision | None = None,
    do_expand_code: bool = False,
    session: SQLAlchemySession | None = None,
) -> TransformationRevision:
    if updated_transformation_revision.type == Type.COMPONENT:
        updated_transformation_revision.content = update_code(updated_transformation_revision)
        if do_expand_code:
            updated_transformation_revision.content = expand_code(updated_transformation_revision)
        return updated_transformation_revision

    assert isinstance(  # noqa: S101
        updated_transformation_revision.content, WorkflowContent
    )  # hint for mypy

    # keep each operator's deprecation flag in sync with the referenced transformation,
    # so that operators referencing an already-deprecated transformation are flagged even
    # when they enter the db via import rather than through pass_on_deprecation
    if session is not None:
        refresh_deprecated_operator_states(session, updated_transformation_revision.content)

    if existing_transformation_revision is not None:
        assert isinstance(  # noqa: S101
            existing_transformation_revision.content, WorkflowContent
        )  # hint for mypy

        existing_operator_ids: list[UUID] = []
        for operator in existing_transformation_revision.content.operators:
            existing_operator_ids.append(operator.id)

        for operator in updated_transformation_revision.content.operators:
            if operator.type == Type.WORKFLOW and operator.id not in existing_operator_ids:
                operator.state = (
                    State.DISABLED
                    if contains_deprecated(operator.transformation_id)
                    else operator.state
                )
    return updated_transformation_revision


class ComponentImportComponentError(ValueError):
    pass


class ComponentImportNonExistingComponentError(ComponentImportComponentError):
    pass


class ReleasedComponentCannotImportDraftComponentError(ComponentImportComponentError):
    pass


def check_direct_component_imports(
    component: TransformationRevision,
    allow_everything_for_draft_components: bool = True,
    check_releasability: bool = False,
    session: SQLAlchemySession | None = None,
) -> None:
    """Checks whether direct component imports in components are valid

    By default, checks are only done for a non-draft component, i.e. in a DRAFT
    component everything is allowed. Set allow_everything_for_draft_components to
    False if you also want to check DRAFT components.

    Checks direct imports, not recursively! In particular, does not check
    for import cycles.

    This is meant to be run on putting (create, update) of component revisions.

    Raises a variant of ComponentImportComponentError if something is wrong.
    Otherwise just returns None.

    Since this requires database access, it is not part of the
    TransformationRevision model validation.

    Requires that direct component imports
    * can be parsed / read from code
    * all exist
    * are all components
    * are all released if the component itself is released or if
      check_releasability is True
    """

    if allow_everything_for_draft_components and component.state is State.DRAFT:
        # allow everything for DRAFT components
        return

    assert isinstance(component.content, str)  # noqa: S101 # for mypy
    try:
        direct_import_ids = get_global_component_imports(component.content)
    except CodeParsingException as e:
        raise ComponentImportComponentError(
            f"Could not parse component code for component {component.name}"
            f" ({component.version_tag}) with id  {component.id} while checking"
            " direct imports"
        ) from e

    try:
        # without caching, as this is/should not be run
        # during execution requests:
        direct_import_trafos = read_multiple_transformation_revisions_by_id(
            tuple(direct_import_ids), session=session
        )
    except DBNotFoundError as e:
        raise ComponentImportNonExistingComponentError(
            f"While checking direct component imports for component {component.name}"
            f" ({component.version_tag}) with id  {component.id}, one of the imported"
            "trafos could not be loaded from database."
        ) from e

    for trafo in direct_import_trafos.values():
        if not trafo.type is Type.COMPONENT:
            raise ComponentImportComponentError(
                f"The component {component.name} ({component.version_tag}) with id"
                f" {component.id} imports a trafo in its code that is not a component:"
                f" {trafo.name} ({trafo.version_tag} with id {trafo.id})"
            )
        if (
            component.state is not State.DRAFT or check_releasability
        ) and trafo.state is State.DRAFT:
            raise ReleasedComponentCannotImportDraftComponentError(
                f"The component {component.name} ({component.version_tag}) with id"
                f" {component.id} is released or should be released, but its code imports"
                f" a DRAFT component: {trafo.name} ({trafo.version_tag} with id {trafo.id})"
            )


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
                **existing_transformation_revision.model_dump()
            )
            updated_transformation_revision.deprecate()
            # prevent overwriting content during deprecating
            updated_transformation_revision.content = existing_transformation_revision.content
    return updated_transformation_revision


def update_or_create_single_transformation_revision(
    transformation_revision: TransformationRevision,
    allow_overwrite_released: bool = False,
    update_component_code: bool = True,
    expand_component_code: bool = False,
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
        if transformation_revision.type is Type.COMPONENT:
            # may raise ComponentImportComponentError
            check_direct_component_imports(
                transformation_revision, session=session
            )  # in particular checks all imports are released if component is RELEASED

        try:
            existing_transformation_revision = select_tr_by_id(
                session, transformation_revision.id, log_error=False
            )
        except DBNotFoundError:
            if transformation_revision.type == Type.WORKFLOW or update_component_code:
                transformation_revision = update_content(
                    transformation_revision,
                    do_expand_code=expand_component_code,
                    session=session,
                )

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
                    transformation_revision,
                    existing_transformation_revision,
                    do_expand_code=expand_component_code,
                    session=session,
                )

            update_tr(session, transformation_revision)

        # Build the nesting for workflows regardless of state. This must happen even for
        # DISABLED workflows: a deprecated workflow is still executable, and a workflow
        # can enter the db already in DISABLED state (e.g. importing a pre-deprecated
        # workflow), in which case it was never stored as RELEASED and would otherwise
        # never get its nesting populated -> execution would fail to resolve its operators.
        if transformation_revision.type == Type.WORKFLOW:
            assert isinstance(  # noqa: S101
                transformation_revision.content, WorkflowContent
            )  # hint for mypy
            update_nesting(session, transformation_revision.id, transformation_revision.content)

        if transformation_revision.state == State.DISABLED:
            pass_on_deprecation(session, transformation_revision.id)

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
    """Determine if transformation revision is unused in non-deprecated workflows.

    More precisely: Determine if specified transformation revision is only contained in
    transformation revisions which are deprecated, i.e. have the state DISABLED.

    This does not check for component imports!
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


def filter_unused_transformation_ids(transformation_ids: list[UUID]) -> set[UUID]:
    """Return the subset of the given transformation ids that are unused.

    A transformation revision is considered unused if it is only contained in
    deprecated (DISABLED) workflows, i.e. it is not contained in any non-deprecated
    workflow (see is_unused). This computes the result for all given ids with a single
    query instead of one transaction per id.

    This does not check for component imports!
    """
    if not transformation_ids:
        return set()

    with get_session()() as session, session.begin():
        # ids that ARE used: they appear as a nested transformation in at least one
        # non-deprecated containing workflow
        used_ids = set(
            session.execute(
                select(distinct(NestingDBModel.nested_transformation_id))
                .join(
                    TransformationRevisionDBModel,
                    TransformationRevisionDBModel.id == NestingDBModel.workflow_id,
                )
                .where(NestingDBModel.nested_transformation_id.in_(transformation_ids))
                .where(TransformationRevisionDBModel.state != State.DISABLED)
            )
            .scalars()
            .all()
        )

    return {tr_id for tr_id in transformation_ids if tr_id not in used_ids}


def get_distinct_categories(types: set[Type] | None = None) -> list[str]:
    """Get unique categories of all trafo revisions of specified types

    This is used for example by the component adapter to obtain thing nodes
    """
    types_to_query = [t.value for t in Type] if types is None else list(types)

    with get_session()() as session, session.begin():
        categories = session.execute(
            select(TransformationRevisionDBModel.category)
            .filter(TransformationRevisionDBModel.type.in_(types_to_query))
            .distinct()
        )
        results = list(categories.scalars().all())

    return results


def multiple_trafo_select_filtered(
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    revision_group_id: UUID | None = None,
    ids: list[UUID] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
    states: list[State] | None = None,
) -> Select:
    selection = select(TransformationRevisionDBModel)

    if type is not None:
        selection = selection.where(TransformationRevisionDBModel.type == type)
    if state is not None:
        selection = selection.where(TransformationRevisionDBModel.state == state)
    if states is not None:
        selection = selection.where(TransformationRevisionDBModel.state.in_(states))
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

    return selection


def select_multiple_transformation_revision_stubs(
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    revision_group_id: UUID | None = None,
    ids: list[UUID] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
    states: list[State] | None = None,
) -> list[TransformationRevisionStub]:
    """Filterable selection of transformation revision stubs from db

    Only the columns for a TransformationRevisionStub are loaded from db.
    """
    with get_session()() as session, session.begin():
        selection = multiple_trafo_select_filtered(
            type=type,
            state=state,
            categories=categories,
            category_prefix=category_prefix,
            revision_group_id=revision_group_id,
            ids=ids,
            names=names,
            include_deprecated=include_deprecated,
            states=states,
        )
        selection = selection.options(
            load_only(
                TransformationRevisionDBModel.id,
                TransformationRevisionDBModel.revision_group_id,
                TransformationRevisionDBModel.name,
                TransformationRevisionDBModel.description,
                TransformationRevisionDBModel.category,
                TransformationRevisionDBModel.version_tag,
                TransformationRevisionDBModel.disabled_timestamp,
                TransformationRevisionDBModel.released_timestamp,
                TransformationRevisionDBModel.state,
                TransformationRevisionDBModel.type,
                TransformationRevisionDBModel.io_interface,
            )
        )
        results = session.execute(selection).scalars().all()

        return [TransformationRevisionStub.from_orm_model(result) for result in results]


def select_multiple_transformation_revisions(
    type: Type | None = None,  # noqa: A002
    state: State | None = None,
    categories: list[ValidStr] | None = None,
    category_prefix: ValidStr | None = None,
    revision_group_id: UUID | None = None,
    ids: list[UUID] | None = None,
    names: list[NonEmptyValidStr] | None = None,
    include_deprecated: bool = True,
    states: list[State] | None = None,
) -> list[TransformationRevision]:
    """Filterable selection of transformation revisions from db"""

    with get_session()() as session, session.begin():
        selection = multiple_trafo_select_filtered(
            type=type,
            state=state,
            categories=categories,
            category_prefix=category_prefix,
            revision_group_id=revision_group_id,
            ids=ids,
            names=names,
            include_deprecated=include_deprecated,
            states=states,
        )

        results = session.execute(selection).scalars().all()

        return [TransformationRevision.from_orm_model(result) for result in results]


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
        unused_ids = filter_unused_transformation_ids([tr.id for tr in tr_list])
        tr_list = [tr for tr in tr_list if tr.id in unused_ids]

    if params.include_dependencies:
        dependencies = []
        already_included_trafo_ids = {tr.id for tr in tr_list}
        for tr in tr_list:
            if tr.type == Type.WORKFLOW:
                nested_tr_dict = get_all_nested_transformation_revisions(tr, allow_caching=False)
                for nested_trafo_id in nested_tr_dict:
                    if nested_trafo_id not in already_included_trafo_ids:
                        already_included_trafo_ids.add(nested_trafo_id)
                        dependencies.append(nested_tr_dict[nested_trafo_id])
        tr_list = tr_list + dependencies

        # obtain imported components for all components, recusively
        components = [tr for tr in tr_list if tr.type is Type.COMPONENT]

        imported_components_by_id = read_component_imports_recursively(components)
        tr_list = tr_list + list(imported_components_by_id.values())

    return tr_list


def nof_db_entries() -> int:
    with get_session()() as session, session.begin():
        nof_rows: int = session.query(TransformationRevisionDBModel.id).count()
        logger.info("DB contains %s rows", str(nof_rows))

    return nof_rows


def get_all_nested_transformation_revisions(
    transformation_revision: TransformationRevision, allow_caching: bool = True
) -> dict[UUID, TransformationRevision]:
    """Obtain nested (recursive) trafo revisions

    transformation_revision is required to be of type WORKFLOW.

    Returns a dict of form nested trafo id: nested_trafo.

    "all" means that this recursively provides all trafo revs that occur from
    possibly multiple nesting levels.
    """
    if transformation_revision.type != Type.WORKFLOW:
        msg = (
            f"cannot get operators of transformation revision {transformation_revision.id} "
            f"because its type is not WORKFLOW"
        )
        logger.error(msg)
        raise TypeConflict(msg)

    with get_session()() as session, session.begin():
        descendants = find_all_nested_transformation_revisions(session, transformation_revision.id)

        nested_trafos_by_id = (
            read_multiple_transformation_revisions_by_id_with_possible_caching
            if allow_caching
            else read_multiple_transformation_revisions_by_id
        )(
            tuple(descendant.transformation_id for descendant in descendants),  # noqa: UP034
            session=session,
        )

    return nested_trafos_by_id


def get_latest_revision_id(revision_group_id: UUID) -> UUID:
    # Select only the id of the newest released revision instead of loading every
    # released revision of the group (with full content) and sorting in Python.
    with get_session()() as session, session.begin():
        latest_revision_id: UUID | None = session.execute(
            select(TransformationRevisionDBModel.id)
            .where(
                TransformationRevisionDBModel.revision_group_id == revision_group_id,
                TransformationRevisionDBModel.state == State.RELEASED,
            )
            .order_by(TransformationRevisionDBModel.released_timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

    if latest_revision_id is None:
        msg = (
            f"no released transformation revisions with revision group id {revision_group_id} "
            f"found in the database"
        )
        logger.error(msg)
        raise DBNotFoundError(msg)

    return latest_revision_id
