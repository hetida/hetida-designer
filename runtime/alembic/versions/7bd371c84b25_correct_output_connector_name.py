"""Correct output connector name

Revision ID: 7bd371c84b25
Revises: 81064642674e
Create Date: 2023-10-04 15:54:55.366910

Update the connector_name attribute of outputs to the correct value if it was incorrectly set
to the default value "connector_name". This has been caused by a faulty implementation in the
get_operator_and_connector_name function.

This function is used to transform WorklfowRevisionFrontendDto instances (previous data model)
to TransformationRevision instances (current data model). The incorrect implementation existed
from release 0.7.1 up to and including release 0.8.8.

Workflows that were updated with release 0.8.9 are not affected. Workflows that were last
updated between release 0.7.1 and 0.8.9 are no longer valid as of release 0.9.0.
Workflows that are in the DRAFT state will have their outputs disappear with the next PUT
request and their execution will fail. The affected
workflows can be automatically repaired using this endpoint instead.
"""
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from pydantic import BaseModel
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import UUIDType

from alembic import op

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "7bd371c84b25"
down_revision = "81064642674e"
branch_labels = None
depends_on = None


class State(StrEnum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    DISABLED = "DISABLED"


class Type(StrEnum):
    COMPONENT = "COMPONENT"
    WORKFLOW = "WORKFLOW"


class DataType(StrEnum):
    Integer = "INT"
    Float = "FLOAT"
    String = "STRING"
    DataFrame = "DATAFRAME"
    Series = "SERIES"
    MultiTSFrame = "MULTITSFRAME"
    Boolean = "BOOLEAN"
    Any = "ANY"
    PlotlyJson = "PLOTLYJSON"


class TransformationRevisionDBModel(Base):
    __tablename__ = "transformation_revisions"

    id: UUIDType = sa.Column(  # noqa: A003
        UUIDType(binary=False), primary_key=True, default=uuid4
    )
    type = sa.Column(sa.Enum(Type), nullable=False)  # noqa: A003
    workflow_content = sa.Column(
        sa.JSON(none_as_null=True), nullable=True, default=lambda: None
    )


class IO(BaseModel):
    id: UUID  # noqa: A003
    name: str | None = None
    data_type: DataType


class InputType(StrEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class InputTypeMixIn(BaseModel):
    type: InputType = InputType.REQUIRED  # noqa: A003
    value: Any | None = None


class Position(BaseModel):
    x: int
    y: int


class Connector(IO):
    position: Position


class OperatorInput(InputTypeMixIn, Connector):
    exposed: bool = False


class OperatorOutput(Connector):
    pass


class Operator(BaseModel):
    id: UUID  # noqa: A003
    revision_group_id: UUID
    name: str
    type: Type  # noqa: A003
    state: State
    version_tag: str
    transformation_id: UUID
    inputs: list[OperatorInput]
    outputs: list[OperatorOutput]
    position: Position


class Vertex(BaseModel):
    """Represents start or end point of a link."""

    operator: UUID | None
    connector: Connector


class Link(BaseModel):
    id: UUID  # noqa: A003
    start: Vertex
    end: Vertex
    path: list[Position] = []


class WorkflowContentIO(Connector):
    operator_id: UUID
    connector_id: UUID
    operator_name: str
    connector_name: str
    position: Position = Position(x=0, y=0)


class WorkflowContentOutput(WorkflowContentIO):
    pass


class WorkflowContentDynamicInput(InputTypeMixIn, WorkflowContentIO):
    pass


class WorkflowContentConstantInput(WorkflowContentIO):
    value: str


class WorkflowContent(BaseModel):
    operators: list[Operator] = []
    links: list[Link] = []
    constants: list[WorkflowContentConstantInput] = []
    inputs: list[WorkflowContentDynamicInput] = []
    outputs: list[WorkflowContentOutput] = []


def upgrade() -> None:
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for workflow_tr in session.query(TransformationRevisionDBModel).where(
        TransformationRevisionDBModel.type == Type.WORKFLOW
    ):
        wf_content = WorkflowContent(**workflow_tr.workflow_content)
        applicable = False
        if len(wf_content.outputs) != 0:
            for output in wf_content.outputs:
                if output.connector_name == "connector_name":
                    applicable = True
                    for operator in wf_content.operators:
                        if operator.id == output.operator_id:
                            for output_connector in operator.outputs:
                                if output_connector.id == output.connector_id:
                                    assert (  # noqa: S101
                                        output_connector.name is not None
                                    )
                                    output.connector_name = output_connector.name
        if applicable:
            update_or_create_transformation_revision(tr, directly_in_db=directly_in_db)


def downgrade() -> None:
    pass
