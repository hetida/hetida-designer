import datetime
from typing import List, Optional, Union, cast
from uuid import UUID, uuid4

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, ValidationError, validator

from hetdesrun.models.code import (
    CodeModule,
    NonEmptyValidStr,
    ShortNonEmptyValidStr,
    ValidStr,
)
from hetdesrun.models.component import ComponentNode, ComponentRevision
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.models.workflow import WorkflowNode
from hetdesrun.persistence.dbmodels import TransformationRevisionDBModel
from hetdesrun.persistence.dbservice.exceptions import DBIntegrityError
from hetdesrun.persistence.models.io import (
    Connector,
    IOConnector,
    IOInterface,
    Position,
)
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type


def transform_to_utc_datetime(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(tz=datetime.timezone.utc)


class TransformationRevision(BaseModel):
    """Either a component revision or a workflow revision

    Both can be instantiated as an operator in a workflow revision
    (yes, workflow in workflow in workflow... is possible) and are therefore
    able to transform input data to output result data.

    Note that there is no actual component or workflow entity, only revisions. Revisions are tied
    together via the group id, and otherwise do not need to have anything in common, i.e. their
    name and their interface etc. can differ completely.

    Revisions with state RELEASED are what makes execution reproducible - they cannot be edited any
    more and only they can be instantiated as operators.

    Additionally RELEASED revisions cannot be deleted, but their state can be changed to
    DISABLED. DISABLED revisions cannot be instantiated as new operators anymore but existing
    operators from them still work (for reproducibility). Note that in the Frontend the DISABLED
    state is called "DEPRECATED". The frontend then allows to replace deprecated operators by other
    (possibly newer) released revisions from the the same revision group (i.e. same group id).
    """

    id: UUID
    revision_group_id: UUID
    name: NonEmptyValidStr
    description: ValidStr = ValidStr("")
    category: NonEmptyValidStr = Field(
        "Other",
        description='Category in which this is classified, i.e. the "drawer" in the User Interface',
    )
    version_tag: ShortNonEmptyValidStr
    released_timestamp: Optional[datetime.datetime] = Field(
        None,
        description="If the revision is RELEASED then this should be release timestamp",
    )

    disabled_timestamp: Optional[datetime.datetime] = Field(
        None,
        description="If the revision is DISABLED then this should be disable/deprecation timestamp",
    )
    state: State = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(State)]),
    )
    type: Type = Field(
        ...,
        description="one of " + ", ".join(['"' + x.value + '"' for x in list(Type)]),
    )

    documentation: str = Field(
        (
            "\n"
            "# New Component/Workflow\n"
            "## Description\n"
            "## Inputs\n"
            "## Outputs\n"
            "## Details\n"
            "## Examples\n"
        ),
        description="Documentation in markdown format.",
    )
    content: Union[str, WorkflowContent] = Field(
        ...,
        description=(
            "Code as string in case of type COMPONENT, "
            "WorkflowContent in case of type WORKFLOW"
        ),
    )

    io_interface: IOInterface = Field(
        ...,
        description=(
            "In case of type WORKFLOW determined from content. "
            "To change from state DRAFT to state RELEASED all inputs and outputs must have names."
        ),
    )

    test_wiring: WorkflowWiring = Field(
        ...,
        description=(
            "The input and output wirings must match "
            "the inputs and outputs of the io_interface"
        ),
    )

    # pylint: disable=no-self-argument,no-self-use
    @validator("version_tag")
    def version_tag_not_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError('version_tag is not allowed to be "latest"')
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("released_timestamp")
    def released_timestamp_to_utc(cls, v: datetime.datetime) -> datetime.datetime:
        if v is None:
            return v
        return transform_to_utc_datetime(v)

    # pylint: disable=no-self-argument,no-self-use
    @validator("disabled_timestamp")
    def disabled_timestamp_to_utc(cls, v: datetime.datetime) -> datetime.datetime:
        if v is None:
            return v
        return transform_to_utc_datetime(v)

    # pylint: disable=no-self-argument,no-self-use
    @validator("state")
    def timestamps_set_if_released_or_disabled(cls, v: State, values: dict) -> State:
        if v is State.RELEASED and (
            "released_timestamp" not in values or values["released_timestamp"] is None
        ):
            raise ValueError("released_timestamp must be set if state is RELEASED")
        if v is State.DISABLED and (
            "disabled_timestamp" not in values or values["disabled_timestamp"] is None
        ):
            raise ValueError("disabled_timestamp must be set if state is DISABLED")
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("content")
    def content_type_correct(
        cls, v: Union[str, WorkflowContent], values: dict
    ) -> Union[str, WorkflowContent]:
        if values["type"] is Type.WORKFLOW and not isinstance(v, WorkflowContent):
            raise ValueError(
                "Content must be of type WorkflowContent for transformation revision"
                " with type WORKFLOW"
            )
        if values["type"] is Type.COMPONENT and not isinstance(v, str):
            raise ValueError(
                "Content must be of type str (representing code) for transformation revision"
                " with type COMPONENT"
            )
        return v

    # pylint: disable=no-self-argument,no-self-use
    @validator("io_interface")
    def io_interface_fits_to_content(
        cls, io_interface: IOInterface, values: dict
    ) -> IOInterface:

        if values["type"] is not Type.WORKFLOW:
            return io_interface

        try:
            workflow_content = values["content"]
            assert isinstance(workflow_content, WorkflowContent)  # hint for mypy
        except KeyError as e:
            raise ValueError(
                "Cannot fit io_interface to content if attribute 'content' is missing"
            ) from e

        io_interface.inputs = [input.to_io() for input in workflow_content.inputs]
        io_interface.outputs = [output.to_io() for output in workflow_content.outputs]

        return io_interface

    # pylint: disable=no-self-argument,no-self-use
    @validator("io_interface")
    def io_interface_no_names_empty(
        cls, io_interface: IOInterface, values: dict
    ) -> IOInterface:

        if values["state"] is not State.RELEASED:
            return io_interface

        for io in io_interface.inputs + io_interface.outputs:
            if io.name is None or io.name == "":
                raise ValueError(
                    "Released transformation revisions may not have empty input or output names!"
                )

        return io_interface

    @validator("test_wiring")
    def test_wiring_fits_to_io_interface(
        cls, test_wiring: WorkflowWiring, values: dict
    ) -> WorkflowWiring:
        if "inputs" in values:
            if len(test_wiring.input_wirings) != len(values["inputs"]):
                raise ValueError(
                    "Number of transformation revision inputs does not match"
                    " number of inputs in test wiring!"
                )
            for input_wiring in test_wiring.input_wirings:
                if input_wiring.workflow_input_name not in [
                    io.name for io in values["inputs"]
                ]:
                    raise ValueError(
                        f"No input of the IO interface matches the "
                        f"input wiring {input_wiring.workflow_input_name}!"
                    )
        if "outputs" in values:
            if len(test_wiring.output_wirings) != len(values["outputs"]):
                raise ValueError(
                    "Number of transformation revision outputs does not match"
                    " number of outputs in test wiring!"
                )
            for output_wiring in test_wiring.output_wirings:
                if output_wiring.workflow_output_name not in [
                    io.name for io in values["outputs"]
                ]:
                    raise ValueError(
                        f"No output of the IO interface matches the "
                        f"output wiring {output_wiring.workflow_output_name}!"
                    )

        return test_wiring

    def release(self) -> None:
        self.released_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.state = State.RELEASED

    def deprecate(self) -> None:
        self.disabled_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.state = State.DISABLED

    def to_component_revision(self) -> ComponentRevision:
        if self.type != Type.COMPONENT:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a component revision since its type is not COMPONENT"
            )
        return ComponentRevision(
            uuid=self.id,
            name=self.name,
            code_module_uuid=self.id,
            function_name="main",
            inputs=[input.to_component_input() for input in self.io_interface.inputs],
            outputs=[
                output.to_component_output() for output in self.io_interface.outputs
            ],
        )

    def to_component_node(self, operator_id: UUID, operator_name: str) -> ComponentNode:
        if self.type != Type.COMPONENT:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a component node since its type is not COMPONENT"
            )
        return ComponentNode(
            id=str(operator_id),
            component_uuid=str(self.id),
            name=operator_name,
        )

    def to_workflow_node(
        self, operator_id: UUID, sub_nodes: List[Union[ComponentNode, WorkflowNode]]
    ) -> WorkflowNode:
        if self.type != Type.WORKFLOW:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a workflow node since its type is not WORKFLOW"
            )
        assert isinstance(self.content, WorkflowContent)  # hint for mypy
        return self.content.to_workflow_node(operator_id, self.name, sub_nodes)

    def to_code_module(self) -> CodeModule:
        if self.type != Type.COMPONENT:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a component revision since its type is not COMPONENT"
            )
        return CodeModule(code=self.content, uuid=self.id)

    def to_operator(self) -> Operator:
        return Operator(
            revision_group_id=self.revision_group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            type=self.type,
            state=State.RELEASED,
            version_tag=self.version_tag,
            transformation_id=self.id,
            inputs=[Connector.from_io(input) for input in self.io_interface.inputs],
            outputs=[Connector.from_io(output) for output in self.io_interface.outputs],
            position=Position(x=0, y=0),
        )

    def to_orm_model(self) -> TransformationRevisionDBModel:
        return TransformationRevisionDBModel(
            id=self.id,
            revision_group_id=self.revision_group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            version_tag=self.version_tag,
            state=self.state,
            type=self.type,
            documentation=self.documentation,
            workflow_content=cast(WorkflowContent, self.content).dict()
            if self.type is Type.WORKFLOW
            else None,
            component_code=cast(str, self.content)
            if self.type is Type.COMPONENT
            else None,
            io_interface=self.io_interface.dict(),
            test_wiring=self.test_wiring.dict(),
            released_timestamp=self.released_timestamp,
            disabled_timestamp=self.disabled_timestamp,
        )

    def wrap_component_in_tr_workflow(self) -> "TransformationRevision":
        operator = self.to_operator()

        wf_inputs = []
        wf_outputs = []
        links = []
        for input_connector in operator.inputs:
            wf_input = IOConnector.from_connector(
                input_connector, operator.id, operator.name
            )
            wf_inputs.append(wf_input)
            link = Link(
                start=Vertex(operator=None, connector=wf_input.to_connector()),
                end=Vertex(operator=operator.id, connector=input_connector),
            )
            links.append(link)
        for output_connector in operator.outputs:
            wf_output = IOConnector.from_connector(
                output_connector, operator.id, operator.name
            )
            wf_outputs.append(wf_output)
            link = Link(
                start=Vertex(operator=operator.id, connector=output_connector),
                end=Vertex(operator=None, connector=wf_output.to_connector()),
            )
            links.append(link)

        return TransformationRevision(
            id=uuid4(),
            revision_group_id=uuid4(),
            name=self.name,
            category=self.category,
            version_tag=self.version_tag,
            released_timestamp=self.released_timestamp,
            disabled_timestamp=self.disabled_timestamp,
            state=self.state,
            type=Type.WORKFLOW,
            content=WorkflowContent(
                inputs=wf_inputs,
                outputs=wf_outputs,
                operators=[operator],
                links=links,
            ),
            io_interface=IOInterface(
                inputs=[input_connector.to_io() for input_connector in wf_inputs],
                outputs=[output_connector.to_io() for output_connector in wf_outputs],
            ),
            test_wiring=self.test_wiring,
        )

    @classmethod
    def from_orm_model(
        cls, orm_model: TransformationRevisionDBModel
    ) -> "TransformationRevision":

        try:
            return TransformationRevision(
                id=orm_model.id,
                revision_group_id=orm_model.revision_group_id,
                name=orm_model.name,
                description=orm_model.description,
                category=orm_model.category,
                version_tag=orm_model.version_tag,
                state=orm_model.state,
                type=orm_model.type,
                documentation=orm_model.documentation,
                content=orm_model.workflow_content
                if orm_model.type is Type.WORKFLOW
                else orm_model.component_code,
                io_interface=orm_model.io_interface,
                test_wiring=orm_model.test_wiring,
                released_timestamp=orm_model.released_timestamp.replace(
                    tzinfo=datetime.timezone.utc
                )
                if orm_model.released_timestamp is not None
                else None,
                disabled_timestamp=orm_model.disabled_timestamp.replace(
                    tzinfo=datetime.timezone.utc
                )
                if orm_model.disabled_timestamp is not None
                else None,
            )
        except ValidationError as e:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(e)}"
            )
            raise DBIntegrityError(msg) from e

    class Config:
        validate_assignment = True
