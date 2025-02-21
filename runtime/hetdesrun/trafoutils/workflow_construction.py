"""Workflow as code construction

Provides a WorkflowConstruction ContextManager that allows to define workflows as code.
"""

import datetime
import json
from functools import cached_property
from types import TracebackType
from typing import Any, Literal
from uuid import UUID, uuid4

from hetdesrun.models.code import NonEmptyValidStr, ShortNonEmptyValidStr, ValidStr
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    OperatorInput,
    OperatorOutput,
    Position,
    WorkflowContentConstantInput,
    WorkflowContentDynamicInput,
    WorkflowContentOutput,
)
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.transformation import (
    TransformationInput,
    TransformationOutput,
    TransformationRevision,
)
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.trafo_collection import TrafoCollection
from hetdesrun.trafoutils.upgrade_operators import order_operator_inputs
from hetdesrun.utils import State, Type


class OperatorInputInfo:
    """Infos about and references around an operator input during workflow construction"""

    def __init__(self, operator: Operator, operator_input: OperatorInput):
        self.operator = operator
        self.operator_input = operator_input
        self.name = self.operator_input.name
        self.data_type = self.operator_input.data_type

        self.inp = operator_input

        self.blocked: bool = False  # whether something (constant, trafo input, link goes into it)

    @property  # cannot be cached since it changes when other op. inputs get exposed/unexposed.
    def position_index(self) -> int:
        """Get the input's position index in the exposed operator inputs

        I.e. first exposed input: 0, second exposed: 1, third exposed: 2
        """
        for ind, op_inp in enumerate([op_inp for op_inp in self.operator.inputs if op_inp.exposed]):
            if op_inp.name == self.name:
                return ind

        raise ValueError(
            f"Input with name {self.name} not found in exposed inputs of operator"
            f"{self.operator.name} {self.operator.id}!"
        )


class OperatorOutputInfo:
    """Infos about and references around an operator output during workflow construction"""

    def __init__(self, operator: Operator, operator_output: OperatorOutput):
        self.operator = operator
        self.operator_output = operator_output
        self.name = self.operator_output.name
        self.data_type = self.operator_output.data_type
        self.outp = operator_output

        self.is_link_start = False
        self.is_trafo_output = False

    @cached_property
    def position_index(self) -> int:
        """Get the outputs position index in the operator outputs

        I.e. first output: 0, second: 1, third: 2
        """
        for ind, op_outp in enumerate(self.operator.outputs):
            if op_outp.name == self.name:
                return ind

        raise ValueError(
            f"Output with name {self.name} not found in operator "
            f"{self.operator.name} {self.operator.id}!"
        )


class OperatorInputInfos:
    """Provides easier accessor as part of OperatorInfo.i attribute"""

    def __init__(self, operator_input_infos_by_name: dict[str, OperatorInputInfo]):
        self.operator_input_infos_by_name = operator_input_infos_by_name

    def __getattr__(self, op_inp_name: str) -> OperatorInputInfo:
        return self.operator_input_infos_by_name[op_inp_name]

    def __getitem__(self, op_inp_name: str) -> OperatorInputInfo:
        return self.operator_input_infos_by_name[op_inp_name]


class OperatorOutputInfos:
    """Provides easier accessor as part of OperatorInfo.o attribute"""

    def __init__(self, operator_output_infos_by_name: dict[str, OperatorOutputInfo]):
        self.operator_output_infos_by_name = operator_output_infos_by_name

    def __getattr__(self, op_outp_name: str) -> OperatorOutputInfo:
        return self.operator_output_infos_by_name[op_outp_name]

    def __getitem__(self, op_outp_name: str) -> OperatorOutputInfo:
        return self.operator_output_infos_by_name[op_outp_name]


class OperatorInfo:
    def __init__(self, op: Operator):
        self.operator = op
        self.operator_input_infos_by_name = {
            op_inp.name: OperatorInputInfo(op, op_inp)
            for op_inp in op.inputs
            if op_inp.name is not None
        }
        self.i = OperatorInputInfos(self.operator_input_infos_by_name)
        self.operator_output_infos_by_name = {
            op_outp.name: OperatorOutputInfo(op, op_outp)
            for op_outp in op.outputs
            if op_outp.name is not None
        }
        self.o = OperatorOutputInfos(self.operator_output_infos_by_name)

    def fix_input_ordering(self) -> None:
        """Fixes the ordering of the operators inputs

        This mutates the underlying operator
        """
        self.operator.inputs = order_operator_inputs(self.operator.inputs)


class LinkInfo:
    """Links between operator inputs/outputs

    Note: This does not handle/describe links between trafo inputs and operator inputs
    or operator outputs and trafo outputs.
    """

    def __init__(self, lnk: Link, op_outp_info: OperatorOutputInfo, op_inp_info: OperatorInputInfo):
        self.link = lnk
        self.op_outp_info = op_outp_info
        self.op_inp_info = op_inp_info


class WorkflowConstructor:
    """Workflow construction context manager


    See e.g. unit tests for usage examples.
    """

    def __init__(
        self,
        trafo_collector: TrafoCollection,
        autoarrange: bool = True,
        id: UUID | None = None,  # noqa: A002
        revision_group_id: UUID | None = None,
        name: NonEmptyValidStr = NonEmptyValidStr("Unnamed"),
        description: ValidStr = ValidStr("no description"),
        category: NonEmptyValidStr = NonEmptyValidStr("Test"),
        version_tag: ShortNonEmptyValidStr = ShortNonEmptyValidStr("0.1.0"),
        disabled_timestamp: datetime.datetime | None = None,
        released_timestamp: datetime.datetime | None = None,
        state: State = State.DRAFT,
        type: Literal[Type.WORKFLOW] = Type.WORKFLOW,  # noqa: A002
        documentation: str = "",
    ):
        self.tc: TrafoCollection = trafo_collector
        self.autoarrange = autoarrange
        self.result: TransformationRevision | None = None  # is set when leaving context

        self._operator_infos_by_id: dict[UUID, OperatorInfo] = {}
        self.links: list[LinkInfo] = []

        self.io_links: list[Link] = []
        self.content_outputs: list[WorkflowContentOutput] = []
        self.content_inputs: list[WorkflowContentDynamicInput] = []
        self.trafo_outputs: list[TransformationOutput] = []
        self.trafo_inputs: list[TransformationInput] = []
        self.constants: list[WorkflowContentConstantInput] = []

        # Trafo Rev properties:
        self.id = id if id else uuid4()
        self.revision_group_id = revision_group_id if revision_group_id else uuid4()
        self.name = name
        self.description = description
        self.category = category
        self.version_tag = version_tag
        self.disabled_timestamp = disabled_timestamp
        self.released_timestamp = released_timestamp
        self.state = state
        self.type = type
        self.documentation = documentation

        self.current_operator_pos_x = 0.0
        self.current_operator_pos_y = 0.0

        self.operator_box_header_height: float = 50.0
        self.operator_content_vertical_free_space_base_height: float = 10.0
        self.operator_output_rect_height: float = 20.0

    def __enter__(self) -> "WorkflowConstructor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.finalize()

    def op(self, trafo: TransformationRevision, name: str | None = None) -> OperatorInfo:
        new_operator_info = OperatorInfo(trafo.to_operator(name=name))
        if self.autoarrange:
            new_operator_info.operator.position = Position(
                x=self.current_operator_pos_x, y=self.current_operator_pos_y
            )
            self.current_operator_pos_x = self.current_operator_pos_x + 700.0
            self.current_operator_pos_y = self.current_operator_pos_y + 300.0
        self._operator_infos_by_id[new_operator_info.operator.id] = new_operator_info
        return new_operator_info

    def link(self, o_outp_info: OperatorOutputInfo, o_inp_info: OperatorInputInfo) -> LinkInfo:
        if o_inp_info.blocked:
            raise ValueError(
                f"Operator input {o_inp_info.name} of operator {o_inp_info.operator.name} "
                f"({o_inp_info.operator.id}) is already occupied by another link, workflow "
                "input or constant."
            )

        if o_outp_info.is_trafo_output:
            raise ValueError(
                f"Operator output {o_outp_info.name} of operator {o_outp_info.operator.name} "
                f"({o_outp_info.operator.id}) is already a workflow output and hence cannot become"
                " start of a link."
            )

        new_link_info = LinkInfo(
            Link(
                start={
                    "operator": o_outp_info.operator.id,
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": o_outp_info.name,
                        "data_type": o_outp_info.data_type,
                        "id": o_outp_info.operator_output.id,
                    },
                },
                end={
                    "operator": o_inp_info.operator.id,
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": o_inp_info.name,
                        "data_type": o_inp_info.data_type,
                        "id": o_inp_info.operator_input.id,
                    },
                },
            ),
            o_outp_info,
            o_inp_info,
        )

        o_inp_info.blocked = True
        o_outp_info.is_link_start = True
        self.links.append(new_link_info)
        return new_link_info

    def output(self, name: str, o_outp_info: OperatorOutputInfo) -> None:
        """Add an output to your workflow from an operator output"""

        if o_outp_info.is_link_start:
            raise ValueError(
                f"Operator output {o_outp_info.name} of operator {o_outp_info.operator.name} "
                f"({o_outp_info.operator.id}) is already a start of a link to another operator's "
                " input and hence cannot become a workflow output"
            )

        output_pos = Position(
            x=o_outp_info.operator.position.x + 450,  # note: operator box has 360 width
            y=(  # will be upper edge
                o_outp_info.operator.position.y
                + self.operator_box_header_height  # height header of operator box (black part)
                + self.operator_content_vertical_free_space_base_height
                # (height light-gray part up to first output)
                + (
                    self.operator_output_rect_height
                    + self.operator_content_vertical_free_space_base_height
                )  # vertical distance between two outputs
                * o_outp_info.position_index
            ),
        )

        wf_output_id = uuid4()

        self.content_outputs.append(
            WorkflowContentOutput(
                id=wf_output_id,
                name=name,
                data_type=o_outp_info.operator_output.data_type,
                operator_id=o_outp_info.operator.id,
                connector_id=o_outp_info.operator_output.id,
                operator_name=o_outp_info.operator.name,
                connector_name=o_outp_info.operator_output.name,
                position=output_pos,
            )
        )

        self.io_links.append(
            Link(
                start={
                    "operator": o_outp_info.operator.id,
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": o_outp_info.name,
                        "data_type": o_outp_info.data_type,
                        "id": o_outp_info.operator_output.id,
                    },
                },
                end={
                    # no operator
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": name,
                        "data_type": o_outp_info.data_type,
                        "id": wf_output_id,
                    },
                },
            )
        )

        self.trafo_outputs.append(
            TransformationOutput(id=wf_output_id, name=name, data_type=o_outp_info.data_type)
        )
        o_outp_info.is_trafo_output = True

    def input(
        self,
        name: str,
        o_inp_info: OperatorInputInfo,
        optional: bool = False,
        default_value: Any | None = None,
    ) -> None:
        """Add an input to your workflow from an operator input

        Automatically exposes the operator input if necessary.

        Important: Positioning of workflow content inputs and reordering of operator
        outputs id deferred to the finalization step
        """

        if o_inp_info.blocked:
            raise ValueError(
                f"Operator input {o_inp_info.name} of operator {o_inp_info.operator.name} "
                f"({o_inp_info.operator.id}) is already occupied by another link, workflow "
                "input or constant."
            )

        wf_input_id = uuid4()

        # Make sure it is exposed at the operator!
        # Note: This requires repositioning operations during finalization of
        #   the workflow:
        #     * Ordering of operator inputs must be corrected:
        #           required inputs
        #           => followed by exposed optional inputs
        #           => followed by remaining optional inputs)
        #     * Computing positioning of workflow content inputs
        o_inp_info.operator_input.exposed = True

        self.content_inputs.append(
            WorkflowContentDynamicInput(
                id=wf_input_id,
                name=name,
                data_type=o_inp_info.operator_input.data_type,
                operator_id=o_inp_info.operator.id,
                connector_id=o_inp_info.operator_input.id,
                operator_name=o_inp_info.operator.name,
                connector_name=o_inp_info.operator_input.name,
                type=InputType.OPTIONAL if optional else InputType.REQUIRED,
                value=(
                    json.dumps(default_value)
                    if not isinstance(default_value, str)
                    else default_value
                )
                if optional
                else None,
            )
        )

        self.io_links.append(
            Link(
                end={
                    "operator": o_inp_info.operator.id,
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": o_inp_info.name,
                        "data_type": o_inp_info.data_type,
                        "id": o_inp_info.operator_input.id,
                    },
                },
                start={
                    # no operator
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": name,
                        "data_type": o_inp_info.data_type,
                        "id": wf_input_id,
                    },
                },
            )
        )
        self.trafo_inputs.append(
            TransformationInput(
                id=wf_input_id,
                name=name,
                data_type=o_inp_info.data_type,
                type=InputType.OPTIONAL if optional else InputType.REQUIRED,
                value=default_value if optional else None,
            )
        )
        o_inp_info.blocked = True

    def constant(self, o_inp_info: OperatorInputInfo, value: str) -> None:
        if o_inp_info.blocked:
            raise ValueError(
                f"Operator input {o_inp_info.name} of operator {o_inp_info.operator.name} "
                f"({o_inp_info.operator.id}) is already occupied by another link, workflow "
                "input or constant."
            )

        wf_constant_id = uuid4()

        o_inp_info.operator_input.exposed = True

        self.constants.append(
            WorkflowContentConstantInput(
                id=wf_constant_id,
                name="",
                data_type=o_inp_info.operator_input.data_type,
                operator_id=o_inp_info.operator.id,
                connector_id=o_inp_info.operator_input.id,
                operator_name=o_inp_info.operator.name,
                connector_name=o_inp_info.operator_input.name,
                value=(json.dumps(value) if not isinstance(value, str) else value),
            )
        )

        self.io_links.append(
            Link(
                end={
                    "operator": o_inp_info.operator.id,
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "name": o_inp_info.name,
                        "data_type": o_inp_info.data_type,
                        "id": o_inp_info.operator_input.id,
                    },
                },
                start={
                    # no operator
                    "connector": {
                        "position": {"x": 0, "y": 0},
                        "data_type": o_inp_info.data_type,
                        "id": wf_constant_id,
                    },
                },
            )
        )

        o_inp_info.blocked = True

    def finalize(self) -> TransformationRevision:
        """Finalize and create TransformationRevision object"""

        for op_info in self._operator_infos_by_id.values():
            op_info.fix_input_ordering()

        for wf_content_inp in self.content_inputs:
            op_info = self._operator_infos_by_id[wf_content_inp.operator_id]
            op_inp_info = op_info.operator_input_infos_by_name[wf_content_inp.connector_name]

            wf_content_inp.position = Position(
                x=op_inp_info.operator.position.x - 270,  # note: operator box has 360 width
                y=(  # will be upper edge
                    op_inp_info.operator.position.y
                    + self.operator_box_header_height  # height header of operator box (black part)
                    + self.operator_content_vertical_free_space_base_height
                    # (height light-gray part up to first output)
                    + (
                        self.operator_output_rect_height
                        + self.operator_content_vertical_free_space_base_height
                    )  # vertical distance between two outputs
                    * op_inp_info.position_index
                ),
            )

        # Note: We heavily rely on validations of TransformationRevision which
        # adds missing WorkflowContent.inputs, WorkflowContent.outputs, WorkflowContent.links
        self.result = TransformationRevision(
            id=self.id,
            revision_group_id=self.revision_group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            version_tag=self.version_tag,
            disabled_timestamp=self.disabled_timestamp,
            released_timestamp=self.released_timestamp,
            state=self.state,
            type=self.type,
            documentation=self.documentation,
            content=WorkflowContent(
                operators=[op_info.operator for op_info in self._operator_infos_by_id.values()],
                links=(  # will be auto-corrected
                    [link_info.link for link_info in self.links] + self.io_links
                ),
                constants=self.constants,
                inputs=self.content_inputs,  # will be auto-corrected
                outputs=self.content_outputs,  # will be auto-corrected
            ),
            io_interface=IOInterface(inputs=self.trafo_inputs, outputs=self.trafo_outputs),
            test_wiring=WorkflowWiring(),
            release_wiring=None,
        )

        self.tc.add(self.result)

        return self.result
