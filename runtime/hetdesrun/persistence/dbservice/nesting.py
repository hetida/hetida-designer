import logging
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import IntegrityError

from hetdesrun.persistence.db_engine_and_session import SQLAlchemySession, get_session
from hetdesrun.persistence.dbmodels import (
    Descendant,
    NestingDBModel,
    TransformationRevisionDBModel,
)
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError, DBNestingCycleDetected
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import Type
from hetdesrun.webservice.config import get_config

logger = logging.getLogger(__name__)


def add_single_nesting(session: SQLAlchemySession, nesting: NestingDBModel) -> None:
    if get_config().log_nestings_and_descendants:
        logger.debug(
            "add nesting of transformation revision %s in workflow %s",
            str(nesting.nested_transformation_id),
            str(nesting.workflow_id),
        )
    # session.add (not session.merge): store_own_nestings deletes all of this workflow's
    # nestings first and skips duplicate descendants, so a row cannot already exist. merge
    # would issue a redundant existence SELECT per row (N+1); add stages the row to be
    # flushed in bulk. Integrity errors are handled where the flush happens (in
    # store_own_nestings).
    session.add(nesting)


def find_all_nested_transformation_revisions(
    session: SQLAlchemySession, workflow_id: UUID
) -> list[Descendant]:
    result = session.execute(
        select(
            NestingDBModel.depth,
            NestingDBModel.nested_transformation_id,
            NestingDBModel.nested_operator_id,
        ).where(NestingDBModel.workflow_id == workflow_id)
    )

    descendants = [
        Descendant(row.depth, row.nested_transformation_id, row.nested_operator_id)
        for row in result.all()
    ]

    if get_config().log_nestings_and_descendants:
        for descendant in descendants:
            logger.debug(
                "transformation revision %s is descendant of workflow %s",
                str(descendant.transformation_id),
                str(workflow_id),
            )

    return descendants


def find_all_nestings(
    session: SQLAlchemySession, nested_transformation_id: UUID
) -> list[NestingDBModel]:
    result = session.execute(
        select(NestingDBModel).where(
            NestingDBModel.nested_transformation_id == nested_transformation_id
        )
    )

    return [row[0] for row in result.all()]


def delete_own_nestings(session: SQLAlchemySession, workflow_id: UUID) -> None:
    if get_config().log_nestings_and_descendants:
        logger.debug("delete nestings of transformation revision %s if existing", str(workflow_id))
    session.execute(delete(NestingDBModel).where(NestingDBModel.workflow_id == workflow_id))


def delete_single_nesting(
    session: SQLAlchemySession,
    workflow_id: UUID,
    via_operator_id: UUID,
    nested_operator_id: UUID,
) -> None:
    session.execute(
        delete(NestingDBModel).where(
            and_(
                NestingDBModel.workflow_id == workflow_id,
                NestingDBModel.via_operator_id == via_operator_id,
                NestingDBModel.nested_operator_id == nested_operator_id,
            )
        )
    )


def store_own_nestings(
    session: SQLAlchemySession, workflow_id: UUID, workflow_content: WorkflowContent
) -> set[Descendant]:
    """Replace the nestings of the workflow by those its operators determine

    They are derived from the nestings of the workflows it contains directly, which must be
    up to date. Returns the descendants of the workflow according to its new nestings.
    """
    if get_config().log_nestings_and_descendants:
        logger.debug("store nestings of workflow %s", str(workflow_id))
    delete_own_nestings(session, workflow_id)

    descendants: set[Descendant] = set()

    # Stage all nestings and flush them in bulk. The try wraps the whole staging phase so
    # that a foreign key violation (e.g. an operator referencing a transformation that is
    # not present) is mapped to DBIntegrityError regardless of whether it surfaces at the
    # explicit flush or at an autoflush triggered by find_all_nested_transformation_revisions
    # -- so callers (e.g. the importer) can handle it per transformation instead of it
    # escaping as a raw IntegrityError.
    try:
        for child in workflow_content.operators:
            add_single_nesting(
                session,
                NestingDBModel(
                    workflow_id=workflow_id,
                    via_transformation_id=child.transformation_id,
                    via_operator_id=child.id,
                    depth=1,
                    nested_transformation_id=child.transformation_id,
                    nested_operator_id=child.id,
                ),
            )
            descendants.add(Descendant(1, child.transformation_id, child.id))
            if child.transformation_id == workflow_id:
                raise DBNestingCycleDetected(
                    f"Direct cycle detected: Trying to insert workflow {workflow_id} into itself"
                )

            if child.type == Type.WORKFLOW:
                child_descendants = find_all_nested_transformation_revisions(
                    session, child.transformation_id
                )
                # The nestings of the child do not record the path below the child's own
                # operators: if the child contains the same workflow more than once, its
                # operators occur as several equal descendants, which would violate the
                # primary key here. Store each only once. Descendants differing only in
                # their transformation revision are different nestings, e.g. if the child
                # contains two revisions of a workflow, which keep the operator ids, and an
                # operator was upgraded in one of them.
                for descendant in set(child_descendants):
                    add_single_nesting(
                        session,
                        NestingDBModel(
                            workflow_id=workflow_id,
                            via_transformation_id=child.transformation_id,
                            via_operator_id=child.id,
                            depth=1 + descendant.depth,
                            nested_transformation_id=descendant.transformation_id,
                            nested_operator_id=descendant.operator_id,
                        ),
                    )
                    descendants.add(
                        Descendant(
                            1 + descendant.depth,
                            descendant.transformation_id,
                            descendant.operator_id,
                        )
                    )

        session.flush()
    except IntegrityError as e:
        msg = (
            f"Integrity error while storing nestings for transformation revision "
            f"with id {workflow_id}. Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e

    return descendants


def update_nesting(
    session: SQLAlchemySession, workflow_id: UUID, workflow_content: WorkflowContent
) -> None:
    """Store the nestings of the workflow and update those of the workflows containing it

    The nestings of a workflow are derived from those of the workflows it contains directly.
    So if the transformation revisions nested in a workflow change, e.g. by adding, removing
    or upgrading an operator of a DRAFT workflow, the nestings of all workflows containing it
    change as well. Otherwise e.g. executing them would fail. They are updated from the
    innermost to the outermost.
    """
    if get_config().log_nestings_and_descendants:
        logger.debug("update nesting of workflow %s", str(workflow_id))
    previous_descendants = set(find_all_nested_transformation_revisions(session, workflow_id))
    descendants = store_own_nestings(session, workflow_id, workflow_content)

    # check ancestors to disallow possible introduction of cycles

    disallowed_ancestors = {workflow_id} | {
        descendant.transformation_id for descendant in descendants
    }
    sup_nestings = find_all_nestings(session, workflow_id)
    for ancestor in sup_nestings:
        if ancestor.workflow_id in disallowed_ancestors:
            raise DBNestingCycleDetected(
                f"Cycle detected: This workflow {ancestor.nested_transformation.name}"
                f" ({ancestor.nested_transformation.version_tag})) with id {workflow_id} depends"
                f" on {ancestor.workflow.name} ({ancestor.workflow.version_tag}) with id"
                f" {ancestor.workflow_id}"
                f" but occurs as a dependency of it as well!"
            )

    if descendants == previous_descendants:
        return

    # A workflow containing another one which contains this workflow contains it at a
    # greater depth than the other one does. So ordered by the maximal depth, the nestings
    # of each workflow are derived from up to date nestings of the workflows it contains.
    containing_workflow_ids = list(
        session.execute(
            select(NestingDBModel.workflow_id)
            .where(NestingDBModel.nested_transformation_id == workflow_id)
            .group_by(NestingDBModel.workflow_id)
            .order_by(func.max(NestingDBModel.depth))
        ).scalars()
    )
    for containing_workflow_id in containing_workflow_ids:
        containing_workflow_content = session.execute(
            select(TransformationRevisionDBModel.workflow_content).where(
                TransformationRevisionDBModel.id == containing_workflow_id
            )
        ).scalar_one()
        store_own_nestings(
            session,
            containing_workflow_id,
            WorkflowContent.model_validate(containing_workflow_content),
        )


def update_or_create_nesting(transformation_revision: TransformationRevision) -> None:
    if transformation_revision.type == Type.WORKFLOW:
        with get_session()() as session, session.begin():
            assert isinstance(  # noqa: S101
                transformation_revision.content, WorkflowContent
            )  # hint for mypy

            update_nesting(session, transformation_revision.id, transformation_revision.content)
