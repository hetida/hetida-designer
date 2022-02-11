from typing import List, cast
import logging
from uuid import UUID

from sqlalchemy import select, delete, and_
from sqlalchemy.exc import IntegrityError

from hetdesrun.utils import Type

from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError

from hetdesrun.persistence import SQLAlchemySession, Session
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.persistence.dbmodels import NestingDBModel, Descendant

logger = logging.getLogger(__name__)


def add_single_nesting(session: SQLAlchemySession, nesting: NestingDBModel) -> None:
    try:
        session.add(nesting)
    except IntegrityError as e:
        msg = (
            f"Integrity Error while trying to store nesting for"
            f" transformation revision with id {nesting.workflow_id}."
            f" Error was:\n{str(e)}"
        )
        logger.error(msg)
        raise DBIntegrityError(msg) from e


def find_all_nested_transformation_revisions(
    session: SQLAlchemySession, workflow_id: UUID
) -> List[Descendant]:
    result = session.execute(
        select(
            NestingDBModel.depth,
            NestingDBModel.nested_transformation_id,
            NestingDBModel.nested_operator_id,
        ).where(NestingDBModel.workflow_id == workflow_id)
    )

    return [
        Descendant(row.depth, row.nested_transformation_id, row.nested_operator_id)
        for row in result.all()
    ]


def find_all_nesting_transformation_revisions(
    session: SQLAlchemySession, nested_transformation_id: UUID
) -> List[NestingDBModel]:
    result = session.execute(
        select(NestingDBModel).where(
            NestingDBModel.nested_transformation_id == nested_transformation_id
        )
    )

    return [row[0] for row in result.all()]


def delete_own_nestings(session: SQLAlchemySession, workflow_id: UUID) -> None:
    session.execute(
        delete(NestingDBModel).where(NestingDBModel.workflow_id == workflow_id)
    )


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


def update_nesting(
    session: SQLAlchemySession, workflow_id: UUID, workflow_content: WorkflowContent
) -> None:
    # no need to deal with ancestors, workflow draft has none
    delete_own_nestings(session, workflow_id)

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

        if child.type == Type.WORKFLOW:
            descendants = find_all_nested_transformation_revisions(
                session, child.transformation_id
            )
            for descendant in descendants:
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


def update_or_create_nesting(transformation_revision: TransformationRevision) -> None:

    if transformation_revision.type == Type.WORKFLOW:
        with Session() as session, session.begin():

            workflow_id = transformation_revision.id
            workflow_content = cast(WorkflowContent, transformation_revision.content)

            update_nesting(session, workflow_id, workflow_content)
