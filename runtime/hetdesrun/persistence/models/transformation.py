import datetime
import logging
from typing import cast
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, StrictInt, StrictStr, ValidationError, validator

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
    IOInterface,
    OperatorInput,
    OperatorOutput,
    Position,
    TransformationInput,
    TransformationOutput,
    WorkflowContentDynamicInput,
    WorkflowContentOutput,
)
from hetdesrun.persistence.models.link import Link, Vertex
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)


def transform_to_utc_datetime(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(tz=datetime.timezone.utc)


def adjust_tr_inputs_to_not_matching_wf_inputs_and_remove_surplus_tr_inputs(
    tr_inputs: list[TransformationInput],
    wf_inputs_by_id: dict[UUID, WorkflowContentDynamicInput],
) -> None:
    remove_tr_inputs = []
    for tr_input in tr_inputs:
        try:
            wf_input = wf_inputs_by_id[tr_input.id]
        except KeyError:
            logger.warning(
                "For the io interface input '%s' "
                "there is no workflow content input with the same id. "
                "Thus, it will be removed from the io interface.",
                str(tr_input.id),
            )
            remove_tr_inputs.append(tr_input)
            continue
        if not wf_input.matches_trafo_input(tr_input):
            logger.warning(
                "For the io interface input '%s' "
                "the workflow content input with the same id does not match! "
                "Thus, it will be adjusted in the io interface.",
                str(tr_input.id),
            )
            tr_inputs[tr_inputs.index(tr_input)] = wf_input.to_transformation_input()
        del wf_inputs_by_id[tr_input.id]

    for tr_input in remove_tr_inputs:
        tr_inputs.remove(tr_input)


def add_tr_inputs_for_surplus_wf_inputs(
    tr_inputs: list[TransformationInput],
    wf_inputs_by_id: dict[UUID, WorkflowContentDynamicInput],
) -> None:
    for wf_input in wf_inputs_by_id.values():
        logger.warning(
            "Input '%s' is in the worklow content but not in the io interface. "
            "It will be added to the io interface.",
            str(wf_input.id),
        )
        tr_inputs.append(wf_input.to_transformation_input())


def adjust_tr_outputs_to_not_matching_wf_outputs_and_remove_surplus_tr_outputs(
    tr_outputs: list[TransformationOutput],
    wf_outputs_by_id: dict[UUID, WorkflowContentOutput],
) -> None:
    remove_tr_outputs = []
    for tr_output in tr_outputs:
        try:
            wf_output = wf_outputs_by_id[tr_output.id]
        except KeyError:
            logger.warning(
                "For the io interface output '%s' "
                "there is no workflow content output with the same id. "
                "Thus, it will be removed from the io interface.",
                str({tr_output.id}),
            )
            remove_tr_outputs.append(tr_output)
            continue
        if not wf_output.matches_trafo_output(tr_output):
            logger.warning(
                "For the io interface output '%s' "
                "the workflow content output with the same id does not match! "
                "Thus, it will be adjusted in the io interface.",
                str(tr_output.id),
            )
            # TODO: Delete instead of adjust once the frontend has been updated
            tr_outputs[tr_outputs.index(tr_output)] = wf_output.to_transformation_output()
        del wf_outputs_by_id[tr_output.id]

    for tr_output in remove_tr_outputs:
        tr_outputs.remove(tr_output)


def add_trafo_outputs_for_surplus_wf_outputs(
    io_interface_outputs: list[TransformationOutput],
    wf_outputs_by_id: dict[UUID, WorkflowContentOutput],
) -> None:
    for wf_output in wf_outputs_by_id.values():
        logger.warning(
            "Output '%s' is in the worklow content but not in the io interface. "
            "It will be added to the io interface.",
            str(wf_output.id),
        )
        io_interface_outputs.append(wf_output.to_transformation_output())


class TransformationRevision(BaseModel):
    """Either a component revision or a workflow revision

    Both can be instantiated as an operator in a workflow revision
    (yes, workflow in workflow in workflow... is possible) and are therefore
    able to transform input data to output result data.

    Note that there is no actual component or workflow entity, only revisions. Revisions are tied
    together via the group id, and otherwise do not need to have anything in common, i.e. their
    name and their interface etc. can differ completely.

    During the development of a transformation revision it has the state DRAFT and may go through
    stages where it does not meet all requirements e.g. for execution. Therefore, some properties
    are not validated for revisions in DRAFT state and in particular the test_wiring is not
    validated for entities of this class, but instead in the context of execution.

    Revisions with the state RELEASED are what makes the execution reproducible - they cannot be
    edited anymore except for the two attributes test_wiring and documentation, and only they can
    be instantiated as operators.

    Additionally RELEASED revisions cannot be deleted, but their state can be changed to
    DISABLED. DISABLED revisions cannot be instantiated as new operators anymore but existing
    operators from them still work (for reproducibility). Note that in the Frontend the DISABLED
    state is called "DEPRECATED". The frontend then allows to replace deprecated operators by other
    (possibly newer) released revisions from the the same revision group (i.e. same group id).
    """

    id: UUID  # noqa: A003
    revision_group_id: UUID
    name: NonEmptyValidStr
    description: ValidStr = ValidStr("")
    category: NonEmptyValidStr = Field(
        "Other",  # type: ignore[assignment]
        description=(
            'Category in which this is classified, i.e. the "drawer" in the User Interface.'
        ),
    )
    version_tag: ShortNonEmptyValidStr
    disabled_timestamp: datetime.datetime | None = Field(
        None,
        description=(
            "If the revision is DISABLED then this should be disable/deprecation timestamp."
        ),
        example=datetime.datetime.now(datetime.timezone.utc),
    )
    released_timestamp: datetime.datetime | None = Field(
        None,
        description="If the revision is RELEASED then this should be release timestamp.",
        example=datetime.datetime.now(datetime.timezone.utc),
    )
    state: State = Field(
        ...,
        description="one of " + ", ".join(['"' + str(x) + '"' for x in list(State)]),
    )
    type: Type = Field(  # noqa: A003
        ...,
        description="one of " + ", ".join(['"' + str(x) + '"' for x in list(Type)]),
    )

    documentation: str = Field(
        (
            "# New Component/Workflow\n"
            "## Description\n"
            "## Inputs\n"
            "## Outputs\n"
            "## Details\n"
            "## Examples\n"
        ),
        description="Documentation in markdown format.",
    )
    content: str | WorkflowContent = Field(
        ...,
        description=(
            "Code as string in case of type COMPONENT, " "WorkflowContent in case of type WORKFLOW."
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
            "To enable execution the input and output wirings must match "
            "the inputs and outputs of the io_interface, which is validated "
            "in the scope of the execution."
        ),
    )

    release_wiring: WorkflowWiring | None = Field(
        None,
        description=(
            "Wiring that is stored during release. This allows to reset to a fixed wiring."
            " And to use a fixed wiring for dashboarding."
        ),
    )

    @validator("version_tag")
    def version_tag_not_latest(cls, v: str) -> str:
        if v.lower() == "latest":
            raise ValueError('version_tag is not allowed to be "latest"')
        return v

    @validator("disabled_timestamp")
    def disabled_timestamp_to_utc(cls, v: datetime.datetime) -> datetime.datetime:
        """Transform disabled timestamp to UTC timestamp"""
        if v is None:
            return v
        return transform_to_utc_datetime(v)

    @validator("released_timestamp")
    def released_timestamp_to_utc(cls, v: datetime.datetime) -> datetime.datetime:
        """Transform released timestamp to UTC timestamp"""
        if v is None:
            return v
        return transform_to_utc_datetime(v)

    @validator("released_timestamp", always=True)
    def disabled_timestamp_requires_released_timestamp(
        cls, v: datetime.datetime, values: dict
    ) -> datetime.datetime:
        """Generate released timestamp to disabled timestamp if unset"""
        if (
            "disabled_timestamp" in values
            and values["disabled_timestamp"] is not None
            and v is None
        ):
            logger.warning(
                "Set released_timestamp to disabled_timestamp for "
                "disabled transformation without released_timestamp."
            )
            return values["disabled_timestamp"]
        return v

    @validator("state")
    def timestamps_set_corresponding_to_state(cls, v: State, values: dict) -> State:
        if v is State.DRAFT and (
            "released_timestamp" in values and values["released_timestamp"] is not None
        ):
            raise ValueError("released_timestamp must not be set if state is DRAFT")
        if v is State.RELEASED and (
            "released_timestamp" not in values or values["released_timestamp"] is None
        ):
            raise ValueError("released_timestamp must be set if state is RELEASED")
        if v is State.RELEASED and (
            "disabled_timestamp" in values and values["disabled_timestamp"] is not None
        ):
            raise ValueError("disabled_timestamp must not be set if state is RELEASED")
        if v is State.DISABLED and (
            "disabled_timestamp" not in values or values["disabled_timestamp"] is None
        ):
            raise ValueError("disabled_timestamp must be set if state is DISABLED")
        return v

    @validator("content")
    def content_type_correct(cls, v: str | WorkflowContent, values: dict) -> str | WorkflowContent:
        try:
            type_ = values["type"]
        except KeyError as error:
            raise ValueError(
                "Cannot check if the content type is correct if the attribute 'type' is missing!"
            ) from error

        if type_ is Type.WORKFLOW and not isinstance(v, WorkflowContent):
            raise ValueError(
                "Content must be of type WorkflowContent for transformation revision"
                " with type WORKFLOW"
            )
        if type_ is Type.COMPONENT and not isinstance(v, str):
            raise ValueError(
                "Content must be of type str (representing code) for transformation revision"
                " with type COMPONENT"
            )
        return v

    @validator("io_interface")
    def io_interface_fits_to_content(  # noqa: PLR0912
        cls, io_interface: IOInterface, values: dict
    ) -> IOInterface:
        try:
            type_ = values["type"]
            workflow_content = values["content"]
        except KeyError as error:
            raise ValueError(
                "Cannot fit io_interface to content if any of the attributes "
                "'type', 'content' is missing!"
            ) from error

        if type_ is not Type.WORKFLOW:
            return io_interface

        assert isinstance(  # noqa: S101
            workflow_content, WorkflowContent
        )  # hint for mypy

        wf_inputs_by_id: dict[UUID, WorkflowContentDynamicInput] = {
            wf_input.id: wf_input for wf_input in workflow_content.inputs
        }
        # TODO: Delete instead of adjust once frontend has been updated
        adjust_tr_inputs_to_not_matching_wf_inputs_and_remove_surplus_tr_inputs(
            io_interface.inputs, wf_inputs_by_id
        )
        add_tr_inputs_for_surplus_wf_inputs(io_interface.inputs, wf_inputs_by_id)

        wf_outputs_by_id: dict[UUID, WorkflowContentOutput] = {
            wf_output.id: wf_output for wf_output in workflow_content.outputs
        }
        # TODO: Delete instead of adjust once frontend has been updated
        adjust_tr_outputs_to_not_matching_wf_outputs_and_remove_surplus_tr_outputs(
            io_interface.outputs,
            wf_outputs_by_id,
        )
        add_trafo_outputs_for_surplus_wf_outputs(
            io_interface.outputs,
            wf_outputs_by_id,
        )

        return io_interface

    @validator("io_interface")
    def io_interface_no_names_empty(cls, io_interface: IOInterface, values: dict) -> IOInterface:
        try:
            state = values["state"]
        except KeyError as error:
            raise ValueError(
                "Cannot validate that no names in io_interface are empty "
                "if attribute 'state' is missing!"
            ) from error

        if state is State.DRAFT:
            return io_interface

        for io in io_interface.inputs + io_interface.outputs:
            if io.name is None or io.name == "":
                raise ValueError(
                    "Released transformation revisions may not have empty input or output names!"
                )

        return io_interface

    def release(self) -> None:
        self.released_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.release_wiring = self.test_wiring
        self.state = State.RELEASED

    def deprecate(self) -> None:
        self.disabled_timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.state = State.DISABLED

    def strip_wirings(
        self,
        strip_wiring: bool = False,
        strip_release_wiring: bool = False,
        strip_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
        keep_only_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
        strip_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
        keep_only_release_wirings_with_adapter_ids: set[StrictInt | StrictStr] | None = None,
    ) -> None:
        """Strip wirings as parametrized"""
        if strip_wirings_with_adapter_ids is None:
            strip_wirings_with_adapter_ids = set()

        if keep_only_wirings_with_adapter_ids is None:
            keep_only_wirings_with_adapter_ids = set()

        if strip_release_wirings_with_adapter_ids is None:
            strip_release_wirings_with_adapter_ids = set()

        if keep_only_release_wirings_with_adapter_ids is None:
            keep_only_release_wirings_with_adapter_ids = set()

        if strip_wiring:
            self.test_wiring = WorkflowWiring()

        if strip_release_wiring:
            self.release_wiring = None

        if len(strip_wirings_with_adapter_ids) != 0:
            self.test_wiring.input_wirings = [
                inp_wiring
                for inp_wiring in self.test_wiring.input_wirings
                if inp_wiring.adapter_id not in strip_wirings_with_adapter_ids
            ]
            self.test_wiring.output_wirings = [
                outp_wiring
                for outp_wiring in self.test_wiring.output_wirings
                if outp_wiring.adapter_id not in strip_wirings_with_adapter_ids
            ]
        if len(keep_only_wirings_with_adapter_ids) != 0:
            self.test_wiring.input_wirings = [
                inp_wiring
                for inp_wiring in self.test_wiring.input_wirings
                if inp_wiring.adapter_id in keep_only_wirings_with_adapter_ids
            ]
            self.test_wiring.output_wirings = [
                outp_wiring
                for outp_wiring in self.test_wiring.output_wirings
                if outp_wiring.adapter_id in keep_only_wirings_with_adapter_ids
            ]

        if len(strip_release_wirings_with_adapter_ids) != 0 and self.release_wiring is not None:
            self.release_wiring.input_wirings = [
                inp_wiring
                for inp_wiring in self.release_wiring.input_wirings
                if inp_wiring.adapter_id not in strip_release_wirings_with_adapter_ids
            ]
            self.release_wiring.output_wirings = [
                outp_wiring
                for outp_wiring in self.release_wiring.output_wirings
                if outp_wiring.adapter_id not in strip_release_wirings_with_adapter_ids
            ]
        if len(keep_only_release_wirings_with_adapter_ids) != 0 and self.release_wiring is not None:
            self.release_wiring.input_wirings = [
                inp_wiring
                for inp_wiring in self.release_wiring.input_wirings
                if inp_wiring.adapter_id in keep_only_release_wirings_with_adapter_ids
            ]
            self.release_wiring.output_wirings = [
                outp_wiring
                for outp_wiring in self.release_wiring.output_wirings
                if outp_wiring.adapter_id in keep_only_release_wirings_with_adapter_ids
            ]

    def to_component_revision(self) -> ComponentRevision:
        if self.type != Type.COMPONENT:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a component revision since its type is not COMPONENT"
            )
        return ComponentRevision(
            uuid=self.id,
            name=self.name,
            tag=self.version_tag,
            code_module_uuid=self.id,
            function_name="main",
            inputs=[inp.to_component_input() for inp in self.io_interface.inputs],
            outputs=[output.to_component_output() for output in self.io_interface.outputs],
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
        self,
        operator_id: UUID,
        sub_nodes: list[ComponentNode | WorkflowNode],
    ) -> WorkflowNode:
        if self.type != Type.WORKFLOW:
            raise ValueError(
                f"will not convert transformation revision {self.id}"
                f"into a workflow node since its type is not WORKFLOW"
            )
        assert isinstance(self.content, WorkflowContent)  # hint for mypy # noqa: S101
        return self.content.to_workflow_node(
            transformation_id=self.id,
            transformation_name=self.name,
            transformation_tag=self.version_tag,
            operator_id=operator_id,
            operator_name=self.name,
            sub_nodes=sub_nodes,
        )

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
            type=self.type,
            state=State.RELEASED,
            version_tag=self.version_tag,
            transformation_id=self.id,
            inputs=[
                OperatorInput.from_transformation_input(inp) for inp in self.io_interface.inputs
            ],
            outputs=[
                OperatorOutput.from_transformation_output(output)
                for output in self.io_interface.outputs
            ],
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
            component_code=cast(str, self.content) if self.type is Type.COMPONENT else None,
            io_interface=self.io_interface.dict(),
            test_wiring=self.test_wiring.dict(),
            release_wiring=self.release_wiring.dict() if self.release_wiring is not None else None,
            released_timestamp=self.released_timestamp,
            disabled_timestamp=self.disabled_timestamp,
        )

    def wrap_component_in_tr_workflow(self) -> "TransformationRevision":
        operator = self.to_operator()

        wf_inputs: list[WorkflowContentDynamicInput] = []
        wf_outputs: list[WorkflowContentOutput] = []
        links = []
        for input_connector in operator.inputs:
            wf_input = WorkflowContentDynamicInput.from_operator_input(
                input_connector, operator.id, operator.name
            )
            wf_inputs.append(wf_input)
            link = Link(
                start=Vertex(operator=None, connector=wf_input),
                end=Vertex(operator=operator.id, connector=input_connector),
            )
            links.append(link)
        for output_connector in operator.outputs:
            wf_output = WorkflowContentOutput.from_operator_output(
                output_connector, operator.id, operator.name
            )
            wf_outputs.append(wf_output)
            link = Link(
                start=Vertex(operator=operator.id, connector=output_connector),
                end=Vertex(operator=None, connector=wf_output),
            )
            links.append(link)

        return TransformationRevision(
            id=uuid4(),
            revision_group_id=uuid4(),
            name="COMPONENT EXECUTION WRAPPER WORKFLOW",
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
                inputs=[input_connector.to_transformation_input() for input_connector in wf_inputs],
                outputs=[
                    output_connector.to_transformation_output() for output_connector in wf_outputs
                ],
            ),
            test_wiring=self.test_wiring,
            release_wiring=self.release_wiring,
        )

    @classmethod
    def from_orm_model(cls, orm_model: TransformationRevisionDBModel) -> "TransformationRevision":
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
                release_wiring=orm_model.release_wiring,
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
        except ValidationError as error:
            msg = (
                f"Could not validate db entry for id {orm_model.id}. "
                f"Validation error was:\n{str(error)}"
            )
            raise DBIntegrityError(msg) from error

    class Config:
        validate_assignment = True
