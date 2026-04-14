import logging
from uuid import UUID, uuid4

from hdutils import DataType
from hetdesrun.persistence.models.io import (
    InputType,
    OperatorInput,
    OperatorOutput,
    Position,
    TransformationInput,
    TransformationOutput,
    WorkflowContentDynamicInput,
    WorkflowContentOutput,
)
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.operator import Operator
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.trafoutils.versioning import (
    get_current_revision_for_drafts,
    get_newest_released_trafo_rev,
)
from hetdesrun.utils import State, Type

logger = logging.getLogger(__name__)


def get_connector_end_y_positioning_by_operator_input_name(
    operator: Operator,
    operator_box_header_height: float = 50.0,
    operator_content_vertical_free_space_base_height: float = 10.0,
    operator_input_rect_height: float = 20.0,
) -> dict[str, tuple[float, OperatorInput]]:
    """Compute correct y positions for operator inputs by input name

    Returns:
        Dictionary mapping operator input names that are actually shown
        (which excludes non-exposed optional inputs!) to pairs
            (y_pos, operator_input)
        where y_pos is the position where pathes from links/connectors
        should end.

    Note that y_pos is not in pixels but the abstract unit that the hetida-flowchart
    component uses.
    """

    # Note: uses that
    # * Python dicts keep ordering!
    # * the flowchart component / hd frontend draws operator inputs using the given order
    #   in the received json!

    all_shown_inputs_by_name = {
        op_inp.name: op_inp
        for op_inp in operator.inputs
        if (op_inp.type is InputType.REQUIRED or op_inp.exposed) and op_inp.name is not None
    }

    return {
        op_inp_name: (
            operator.position.y
            + operator_box_header_height  # height header of operator box (black part)
            + operator_content_vertical_free_space_base_height
            # (height light-gray part up to first input)
            + operator_input_rect_height / 2.0  # half-height the input rectangle (to get to middle)
            + y_pos
            # vertical distance between centers of two inputs:
            * (operator_input_rect_height + operator_content_vertical_free_space_base_height),
            op_inp,
        )
        for y_pos, (op_inp_name, op_inp) in enumerate(all_shown_inputs_by_name.items())
    }


def get_connector_start_y_positioning_by_operator_output_name(
    operator: Operator,
    operator_box_header_height: float = 50.0,
    operator_content_vertical_free_space_base_height: float = 10.0,
    operator_output_rect_height: float = 20.0,
) -> dict[str, tuple[float, OperatorOutput]]:
    """Compute correct y positions for operator outputs by output name

    Returns:
        Dictionary mapping operator output names
        to pairs
            (y_pos, operator_output)
        where y_pos is the position where pathes from links/connectors
        should start.

    Note that y_pos is not in pixels but the abstract unit that the hetida-flowchart
    component uses.
    """

    # Note: uses that
    # * Python dicts keep ordering!
    # * the flowchart component / hd frontend draws operator outputs using the given order
    #   in the received json!

    all_shown_outputs_by_name = {
        op_outp.name: op_outp for op_outp in operator.outputs if op_outp.name is not None
    }

    return {
        op_outp_name: (
            operator.position.y
            + operator_box_header_height  # height header of operator box (black part)
            + operator_content_vertical_free_space_base_height
            # (height light-gray part up to first output)
            + operator_output_rect_height
            / 2.0  # half-height the output rectangle (to get to middle)
            + y_pos
            # vertical distance between centers of two outputs:
            * (operator_output_rect_height + operator_content_vertical_free_space_base_height),
            op_outp,
        )
        for y_pos, (op_outp_name, op_outp) in enumerate(all_shown_outputs_by_name.items())
    }


def order_operator_inputs(op_inputs: list[OperatorInput]) -> list[OperatorInput]:
    """Orders operator inputs correctly (REQUIRED first)"""

    required_operator_inputs: list[OperatorInput] = []
    optional_operator_inputs: list[OperatorInput] = []

    for op_inp in op_inputs:
        if op_inp.type is InputType.REQUIRED:
            required_operator_inputs.append(op_inp)
        elif op_inp.type is InputType.OPTIONAL:
            optional_operator_inputs.append(op_inp)
        else:
            raise ValueError(
                f"Operator Input with id {op_inp.id} with name {op_inp.name}"
                f" has invalid type {op_inp.type} for ordering."
            )

    return required_operator_inputs + optional_operator_inputs


def fix_path_end_y_positions(workflow: TransformationRevision, operator: Operator) -> None:
    """Fix link pathes to operator inputs in-place

    Mutates the provided workflow with respect to its given operator!

    If pathes are set for links / connectors into the operator's exposed inputs
    the end node is corrected to the correct y position according to the
    current operator input ordering.

    Note: Links do not need to have a path — the frontend then
    automatically draws a straight line to the correct positions. A path is only
    present if the user edits the link and adds at least one vertex. The path
    always contains the start, at least one vertex and the end.
    """

    y_positions_by_inp_name = get_connector_end_y_positioning_by_operator_input_name(operator)

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    links_into_operator_by_input_name = {
        lnk.end.connector.name: lnk
        for lnk in workflow_content.links
        if lnk.end.operator == operator.id
    }

    for op_inp_name, (y_pos, _) in y_positions_by_inp_name.items():
        lnk = links_into_operator_by_input_name.get(op_inp_name)  # default to None
        if lnk and len(lnk.path) > 0:
            last_position = lnk.path[-1]
            lnk.path = lnk.path[:-1] + [Position(x=last_position.x, y=y_pos)]

    # Note: the lines from workflow inputs to operator inputs
    #   are also links and therefore are corrected by the code above as well!


def fix_path_start_y_positions(workflow: TransformationRevision, operator: Operator) -> None:
    """Fix link pathes from operator outputs in-place

    Mutates the provided workflow with respect to its given operator!

    If pathes are set for links / connectors outof the operator's exposed outputs
    the start node is corrected to the correct y position according to the
    current operator output ordering.

    Note: Links do not need to have a path — the frontend then
    automatically draws a straight line from the correct positions. A path is only
    present if the user edits the link and adds at least one vertex. The path
    always contains the start, at least one vertex and the end.
    """

    y_positions_by_outp_name = get_connector_start_y_positioning_by_operator_output_name(operator)

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    links_outof_operator_by_output_name: dict[str, list[Link]] = {}

    # Note: An operator output can have multiple links starting there.
    for lnk in workflow_content.links:
        if lnk.start.operator == operator.id and lnk.start.connector.name is not None:
            if lnk.start.connector.name not in links_outof_operator_by_output_name:
                links_outof_operator_by_output_name[lnk.start.connector.name] = []
            links_outof_operator_by_output_name[lnk.start.connector.name].append(lnk)

    for op_outp_name, (y_pos, _) in y_positions_by_outp_name.items():
        links = links_outof_operator_by_output_name.get(op_outp_name)  # default to None
        if links is None:
            links = []

        for lnk in links:
            if len(lnk.path) > 0:
                last_position = lnk.path[0]
                lnk.path = [Position(x=last_position.x, y=y_pos)] + lnk.path[1:]

    # Note: the lines from operator outputs to workflow outputs
    #   are also links and therefore are corrected by the code above as well!


def fix_links_into_operator(workflow: TransformationRevision, operator: Operator) -> None:
    """In-place fix links in workflow after operator inputs changed

    Currently this means that only links are kept where all data_types
    still fit strictly: This affects the case when something changes from/to DataType.Any.
    The link is not edited to make it fit these generally allowed cases.
    """
    operator_inputs_by_name = {op_inp.name: op_inp for op_inp in operator.inputs}

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    all_links_to_keep = [
        lnk
        for lnk in workflow_content.links
        if (
            lnk.end.connector.id != operator.id  # keep all links into other operators
            or (
                lnk.end.connector.name in operator_inputs_by_name
                and (lnk.start.connector.data_type is lnk.end.connector.data_type)
                and (
                    lnk.end.connector.data_type
                    is operator_inputs_by_name[lnk.end.connector.name].data_type
                )
            )
        )
    ]

    workflow.content = WorkflowContent.model_construct(
        operators=workflow_content.operators,
        links=all_links_to_keep,  # change only this
        constants=workflow_content.constants,
        inputs=workflow_content.inputs,
        outputs=workflow_content.outputs,
    )


def fix_links_outof_operator(workflow: TransformationRevision, operator: Operator) -> None:
    """In-place fix links in workflow after operator outputs changed

    Currently this means that only links are kept where all data_types
    still fit strictly: This affects the case when something changes from/to DataType.Any.
    The link is not edited to make it fit these generally allowed cases.
    """
    operator_outputs_by_name = {op_outp.name: op_outp for op_outp in operator.outputs}

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    all_links_to_keep = [
        lnk
        for lnk in workflow_content.links
        if (
            lnk.start.connector.id != operator.id  # keep all links outof other operators
            or (
                lnk.start.connector.name in operator_outputs_by_name
                and lnk.end.connector.data_type is lnk.start.connector.data_type
                and lnk.start.connector.data_type
                is operator_outputs_by_name[lnk.start.connector.name].data_type
            )
        )
    ]

    workflow.content = WorkflowContent.model_construct(
        operators=workflow_content.operators,
        links=all_links_to_keep,  # change only this
        constants=workflow_content.constants,
        inputs=workflow_content.inputs,
        outputs=workflow_content.outputs,
    )


def fix_constants(workflow: TransformationRevision, operator: Operator) -> None:
    """In-place fix constants after operator inputs changed"""

    operator_inputs_by_name = {op_inp.name: op_inp for op_inp in operator.inputs}

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    all_constants_to_keep = [
        cst
        for cst in workflow_content.constants
        if (
            cst.operator_id != operator.id  # keep all constants into other operators
            or (
                cst.connector_name in operator_inputs_by_name
                and cst.data_type is operator_inputs_by_name[cst.connector_name].data_type
            )
        )
    ]

    workflow.content = WorkflowContent.model_construct(
        operators=workflow_content.operators,
        links=workflow_content.links,
        constants=all_constants_to_keep,  # change only this
        inputs=workflow_content.inputs,
        outputs=workflow_content.outputs,
    )


def fix_test_wiring_input_wirings(
    workflow: TransformationRevision,
    original_workflow_io_interface_inputs_by_name: dict[str, TransformationInput],
) -> None:
    """In-place fix test wiring after io_interface.inputs changed

    Keeps only those test wiring inputs for which
    * the corresponding (by name) input still exists in workflow.io_interface.inputs
    * the data_type agrees exactly between old and new io_interface input.
    """

    io_interface_inputs_by_name = {inp.name: inp for inp in workflow.io_interface.inputs}

    workflow.test_wiring.input_wirings = [
        inp_wiring
        for inp_wiring in workflow.test_wiring.input_wirings
        if inp_wiring.workflow_input_name in io_interface_inputs_by_name
        and original_workflow_io_interface_inputs_by_name[inp_wiring.workflow_input_name].data_type
        is io_interface_inputs_by_name[inp_wiring.workflow_input_name].data_type
    ]


def fix_test_wiring_output_wirings(
    workflow: TransformationRevision,
    original_workflow_io_interface_outputs_by_name: dict[str, TransformationOutput],
) -> None:
    """In-place fix test wiring after io_interface.outputs changed

    Keeps only those test wiring outputs for which
    * the corresponding (by name) output still exists in workflow.io_interface.outputs
    * the data_type agrees exactly between old and new io_interface output.
    """

    io_interface_outputs_by_name = {outp.name: outp for outp in workflow.io_interface.outputs}

    workflow.test_wiring.output_wirings = [
        outp_wiring
        for outp_wiring in workflow.test_wiring.output_wirings
        if outp_wiring.workflow_output_name in io_interface_outputs_by_name
        and original_workflow_io_interface_outputs_by_name[
            outp_wiring.workflow_output_name
        ].data_type
        is io_interface_outputs_by_name[outp_wiring.workflow_output_name].data_type
    ]


def get_operators_to_check_for_upgrades(
    workflow: TransformationRevision, only_check_deprecated: bool = True
) -> dict[UUID, Operator]:
    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy
    return {
        op.id: op
        for op in workflow_content.operators
        if ((not only_check_deprecated or op.state is State.DISABLED) or op.state is State.DRAFT)
    }


def handle_old_operator_inputs(
    new_trafo_inputs_by_name: dict[str, TransformationInput], operator: Operator
) -> tuple[dict[str, OperatorInput], dict[str, OperatorInput]]:
    """Gathers what needs to be kept for existing operator inputs and what needs to be dropped"""

    to_keep_operator_inputs = []
    operator_inputs_to_remove_connections = {}

    for op_inp in operator.inputs:
        op_inp_name = op_inp.name
        if op_inp_name is None:
            continue
        respective_trafo_inp = new_trafo_inputs_by_name.get(op_inp_name)  # default to None

        if respective_trafo_inp is None:
            # new trafo does not have an input of that name anymore!
            # so we do not add it to the to_keep_operator_inputs
            operator_inputs_to_remove_connections[op_inp_name] = op_inp
            continue

        if (
            respective_trafo_inp.data_type is op_inp.data_type
            or respective_trafo_inp.data_type is DataType.Any
            # types of mapping into this input still fits
        ):
            # in every case make sure the new data_type is correct:
            op_inp.data_type = respective_trafo_inp.data_type

            if respective_trafo_inp.type is not op_inp.type:
                # i.e. changes between REQUIRED / OPTIONAL
                # This is a use case occuring often. links / connections should be
                # preserved then as well if possible.

                # So just update existing operator input and keep the updated operator:
                op_inp.type = respective_trafo_inp.type
                op_inp.exposed = True
                op_inp.value = respective_trafo_inp.value

            to_keep_operator_inputs.append(op_inp)

        else:
            operator_inputs_to_remove_connections[op_inp_name] = op_inp

    to_keep_operator_inputs_by_name = {
        op_inp.name: op_inp for op_inp in to_keep_operator_inputs if op_inp.name is not None
    }
    return to_keep_operator_inputs_by_name, operator_inputs_to_remove_connections


def handle_new_operator_inputs(
    operator: Operator,
    new_trafo: TransformationRevision,
    to_keep_operator_inputs_by_name: dict[str, OperatorInput],
) -> tuple[dict[str, OperatorInput], list[WorkflowContentDynamicInput], list[TransformationInput]]:
    """Gathers changes implied by necessary new operator inputs"""
    new_operator_inputs_by_name = {}

    added_workflow_content_inputs: list[WorkflowContentDynamicInput] = []
    added_workflow_inputs: list[TransformationInput] = []

    for trafo_inp in new_trafo.io_interface.inputs:
        trafo_inp_name = trafo_inp.name
        if trafo_inp_name is None:
            continue
        if not trafo_inp_name in to_keep_operator_inputs_by_name:
            # add new operator input
            new_inp_id = uuid4()
            new_operator_inputs_by_name[trafo_inp_name] = OperatorInput(
                # attributes from OperatorInput class:
                exposed=not (trafo_inp.type is InputType.OPTIONAL),
                # (new inputs are always not exposed if optional)
                # from InputTypeMixin class:
                type=trafo_inp.type,  # InputType (REQUIRED, OPTIONAL)
                value=trafo_inp.value,  # possible default value if OPTIONAL, or None
                # from IO class:
                id=new_inp_id,
                name=trafo_inp_name,
                data_type=trafo_inp.data_type,
                # from Connector class (only present in OperatorInput)
                position=Position(x=0, y=0),
            )

            if trafo_inp.type is not InputType.OPTIONAL:
                new_wf_content_input_id = uuid4()

                new_wf_content_input = WorkflowContentDynamicInput(
                    id=new_wf_content_input_id,
                    type=trafo_inp.type,
                    data_type=trafo_inp.data_type,
                    value=trafo_inp.value,
                    operator_id=operator.id,
                    connector_id=new_inp_id,
                    operator_name=operator.name,
                    connector_name=trafo_inp_name,
                )
                added_workflow_content_inputs.append(new_wf_content_input)

                added_workflow_inputs.append(new_wf_content_input.to_transformation_input())

    return new_operator_inputs_by_name, added_workflow_content_inputs, added_workflow_inputs


def handle_old_operator_outputs(
    new_trafo_outputs_by_name: dict[str, TransformationOutput], operator: Operator
) -> tuple[dict[str, OperatorOutput], dict[str, OperatorOutput]]:
    """Gathers what needs to be kept for existing operator outputs and what needs to be dropped"""

    to_keep_operator_outputs = []
    operator_outputs_to_remove_connections = {}

    for op_outp in operator.outputs:
        op_outp_name = op_outp.name
        if op_outp_name is None:
            continue
        respective_trafo_outp = new_trafo_outputs_by_name.get(op_outp_name)  # default to None

        if respective_trafo_outp is None:
            # new trafo does not have an input of that name anymore!
            # so we do not add it to the to_keep_operator_inputs
            operator_outputs_to_remove_connections[op_outp_name] = op_outp
            continue

        if (
            respective_trafo_outp.data_type is op_outp.data_type
            or respective_trafo_outp.data_type is DataType.Any
            # types of mapping out of this output still fits
        ):
            # in every case make sure the new data_type is correct:
            op_outp.data_type = respective_trafo_outp.data_type

            to_keep_operator_outputs.append(op_outp)
        else:
            operator_outputs_to_remove_connections[op_outp_name] = op_outp

    to_keep_operator_outputs_by_name = {
        op_outp.name: op_outp for op_outp in to_keep_operator_outputs if op_outp.name is not None
    }

    return to_keep_operator_outputs_by_name, operator_outputs_to_remove_connections


def handle_new_operator_outputs(
    operator: Operator,
    new_trafo: TransformationRevision,
    to_keep_operator_outputs_by_name: dict[str, OperatorOutput],
) -> tuple[dict[str, OperatorOutput], list[WorkflowContentOutput], list[TransformationOutput]]:
    """Gathers changes implied by necessary new operator outputs"""

    new_operator_outputs_by_name = {}

    added_workflow_content_outputs: list[WorkflowContentOutput] = []
    added_workflow_outputs: list[TransformationOutput] = []

    for trafo_outp in new_trafo.io_interface.outputs:
        trafo_outp_name = trafo_outp.name
        if trafo_outp_name is None:
            continue

        if not trafo_outp_name in to_keep_operator_outputs_by_name:
            # add new operator output
            new_outp_id = uuid4()
            new_operator_outputs_by_name[trafo_outp_name] = OperatorOutput(
                id=new_outp_id,
                name=trafo_outp_name,
                data_type=trafo_outp.data_type,
                position=Position(x=0, y=0),
            )

            new_wf_output_id = uuid4()
            new_wf_content_output = WorkflowContentOutput(
                id=new_wf_output_id,
                data_type=trafo_outp.data_type,
                operator_id=operator.id,
                connector_id=new_outp_id,
                operator_name=operator.name,
                connector_name=trafo_outp_name,
            )
            added_workflow_content_outputs.append(new_wf_content_output)

            added_workflow_outputs.append(new_wf_content_output.to_transformation_output())
    return new_operator_outputs_by_name, added_workflow_content_outputs, added_workflow_outputs


def upgrade_workflow_operator_in_place(
    workflow: TransformationRevision,
    operator_id: UUID,
    operator: Operator,
    new_trafo: TransformationRevision,
) -> None:
    """Upgrades a single operator in place, mutating the workflow

    Mutates the given workflow and replaces the operator with a new operator
    instantiating the new_trafo.

    Tries to keep all connections and so on if possible.
    """

    original_workflow_io_interface_inputs_by_name = {
        inp.name: inp for inp in workflow.io_interface.inputs if inp.name is not None
    }  # we need to keep track of this since wirings don't know their data_type!

    original_workflow_io_interface_outputs_by_name = {
        outp.name: outp for outp in workflow.io_interface.outputs if outp.name is not None
    }  # we need to keep track of this since wirings don't know their data_type!

    # Change relevant operator attributes in-place
    #   Note: operator.id is kept, otherwise all references would break!
    operator.transformation_id = new_trafo.id
    operator.revision_group_id = new_trafo.revision_group_id
    operator.type = new_trafo.type
    operator.state = new_trafo.state
    operator.version_tag = new_trafo.version_tag

    # okay, so now the whole rest!

    new_trafo_inputs_by_name = {
        inp.name: inp for inp in new_trafo.io_interface.inputs if inp.name is not None
    }
    new_trafo_outputs_by_name = {
        outp.name: outp for outp in new_trafo.io_interface.outputs if outp.name is not None
    }

    to_keep_operator_inputs_by_name, operator_inputs_to_remove_connections = (
        handle_old_operator_inputs(new_trafo_inputs_by_name, operator)
    )

    new_operator_inputs_by_name, added_workflow_content_inputs, added_workflow_inputs = (
        handle_new_operator_inputs(operator, new_trafo, to_keep_operator_inputs_by_name)
    )

    operator.inputs = order_operator_inputs(
        list(to_keep_operator_inputs_by_name.values()) + list(new_operator_inputs_by_name.values())
    )

    fix_links_into_operator(workflow, operator)

    fix_constants(workflow, operator)

    # fix workflow.content.inputs

    workflow_content = workflow.content
    assert isinstance(workflow_content, WorkflowContent)  # noqa: S101 for mypy

    new_workflow_content_inputs = [
        wf_content_input
        for wf_content_input in workflow_content.inputs
        if (wf_content_input.operator_id != operator_id)
        or wf_content_input.connector_name in to_keep_operator_inputs_by_name
    ] + added_workflow_content_inputs  # those from new trafo inputs.

    workflow.content = WorkflowContent.model_construct(
        operators=workflow_content.operators,
        links=workflow_content.links,
        constants=workflow_content.constants,
        inputs=new_workflow_content_inputs,  # changed only this
        outputs=workflow_content.outputs,
    )

    # Fix io_interface.inputs

    wf_content_inputs_by_id = {
        wf_content_inp.id: wf_content_inp for wf_content_inp in workflow.content.inputs
    }

    workflow.io_interface.inputs = [
        inp
        for inp in workflow.io_interface.inputs
        if (
            inp.id in wf_content_inputs_by_id
            and inp.data_type is wf_content_inputs_by_id[inp.id].data_type
        )
    ] + added_workflow_inputs

    fix_test_wiring_input_wirings(workflow, original_workflow_io_interface_inputs_by_name)

    fix_path_end_y_positions(workflow, operator)

    # OUTPUTS

    to_keep_operator_outputs_by_name, operator_outputs_to_remove_connections = (
        handle_old_operator_outputs(new_trafo_outputs_by_name, operator)
    )

    new_operator_outputs_by_name, added_workflow_content_outputs, added_workflow_outputs = (
        handle_new_operator_outputs(operator, new_trafo, to_keep_operator_outputs_by_name)
    )

    operator.outputs = list(to_keep_operator_outputs_by_name.values()) + list(
        new_operator_outputs_by_name.values()
    )

    fix_links_outof_operator(workflow, operator)

    # fix workflow.content.outputs

    new_workflow_content_outputs = [
        wf_content_output
        for wf_content_output in workflow.content.outputs
        if (wf_content_output.operator_id != operator_id)
        or wf_content_output.connector_name in to_keep_operator_outputs_by_name
    ] + added_workflow_content_outputs  # those from new trafo outputs.

    workflow.content = WorkflowContent.model_construct(
        operators=workflow.content.operators,
        links=workflow.content.links,
        constants=workflow.content.constants,
        inputs=workflow.content.inputs,
        outputs=new_workflow_content_outputs,  # changed only this
    )

    # Fix io_interface.outputs

    wf_content_outputs_by_id = {
        wf_content_outp.id: wf_content_outp for wf_content_outp in workflow.content.outputs
    }

    workflow.io_interface.outputs = [
        outp
        for outp in workflow.io_interface.outputs
        if (
            outp.id in wf_content_outputs_by_id
            and outp.data_type is wf_content_outputs_by_id[outp.id].data_type
        )
    ] + added_workflow_outputs

    fix_test_wiring_output_wirings(workflow, original_workflow_io_interface_outputs_by_name)

    fix_path_start_y_positions(workflow, operator)

    # revalidate:
    TransformationRevision(**(workflow.model_dump()))


def upgrade_operators_with_providided_revisions(
    workflow: TransformationRevision,
    possibly_newer_released_trafos_by_trafo_rev_group_id: dict[
        UUID, TransformationRevision | None
    ],  # of form: { revision_group_id : newest_trafo }
    current_revisions_for_draft_operators_by_trafo_id: dict[UUID, TransformationRevision],
    only_check_deprecated: bool = True,
    same_revision_no_op: bool = False,
) -> TransformationRevision:
    """Upgrade operators with provided trafo revisions

    * released/disabled operators are upgraded with given possibly newer trafo
      rev per trafo rev group (possibly_newer_released_trafos_by_trafo_rev_group_id)
      * If the possibly newer is equal to the current operator trafo rev, by default
        the operator is still upgraded. This allows to fix broken operators after
        for example some maintenance operation that changed released trafos' io interface.
        * This behaviout can be turned off by same_revision_no_op.
    * draft operators are upgraded with the current state of the trafo.
      * If the underlying trafo is still a draft, the operator will be upgraded to
        its current state (current_revisions_for_draft_operators_by_trafo_id),
        applying possible changes.
      * If the underlying trafo is now released, the operator will be upgraded to
        its now released state. NOTE: It will not be upgraded to a possibly newer released
        version in the same revision group in this case. To achieve this a second upgrade
        is necessary!
    """

    new_workflow = workflow.model_copy(deep=True)

    operators_to_check = get_operators_to_check_for_upgrades(
        new_workflow, only_check_deprecated=only_check_deprecated
    )

    for op_id, operator in operators_to_check.items():
        if operator.state is State.DRAFT:
            possibly_newer_trafo = current_revisions_for_draft_operators_by_trafo_id.get(
                operator.transformation_id
            )
        else:
            possibly_newer_trafo = possibly_newer_released_trafos_by_trafo_rev_group_id[
                operator.revision_group_id
            ]

        if possibly_newer_trafo is not None:
            if (
                same_revision_no_op
                and possibly_newer_trafo.id == operator.transformation_id
                and not operator.state is State.DRAFT  # always upgrade draft operators!
            ):
                msg = (
                    f"Not handling/upgrading operator {operator.name} ({operator.id}) since"
                    " its transformation id {operator.transformation_id} agrees with the possibly"
                    " newer trafo's id."
                )
                logger.debug(msg)
                continue
            msg = (
                f"Upgrade operator {operator.name} ({operator.id}) with state {operator.state})"
                " with old trafo id"
                f" {operator.transformation_id} to possibly newer trafo"
                f" {possibly_newer_trafo.name} ({possibly_newer_trafo.version_tag})"
                f" with id {possibly_newer_trafo.id}"
            )
            logger.debug(msg)
            upgrade_workflow_operator_in_place(new_workflow, op_id, operator, possibly_newer_trafo)

    return new_workflow


def upgrade_operators_in_workflow(
    trafo: TransformationRevision,
    only_check_deprecated: bool = True,
    use_release_date: bool = False,
    same_revision_no_op: bool = False,
) -> TransformationRevision:
    """Upgrades operators in workflow

    This gathers the necessary transformation revisions for both draft operators
    and released operators and then upgrades them according to the rules described
    in the docstring of upgrade_operators_with_providided_revisions.

    Basically draft operators are upgraded to the current draft state (same revision)
    and released operators are upgraded to the "newest" revision of their trafo rev group.
    """

    if trafo.type is not Type.WORKFLOW:
        raise ValueError(
            f"Transformation {trafo.name} ({trafo.version_tag}) with id {trafo.id} is"
            " not a workflow. Cannot upgrade operators."
        )
    if trafo.state is not State.DRAFT:
        raise ValueError(
            f"Workflow {trafo.name} ({trafo.version_tag}) with id {trafo.id} does"
            " not have state DRAFT. Cannot upgrade operators."
        )

    operators_to_check = get_operators_to_check_for_upgrades(
        trafo, only_check_deprecated=only_check_deprecated
    )

    # map revision_group_id to trafo_rev ids that are requested to be found a newer rev
    trafo_revision_group_ids_to_check_for_newer_released_revs: dict[UUID, list[UUID]] = {}

    draft_trafo_ids = []

    for op in operators_to_check.values():
        if op.state is State.DRAFT:
            draft_trafo_ids.append(op.transformation_id)
        if (
            trafo_revision_group_ids_to_check_for_newer_released_revs.get(  # noqa: SIM910
                op.transformation_id,
                None,
            )
            is None
        ):
            trafo_revision_group_ids_to_check_for_newer_released_revs[op.revision_group_id] = []

        trafo_revision_group_ids_to_check_for_newer_released_revs[op.revision_group_id].append(
            op.transformation_id
        )

    trafo_revision_group_ids_to_check_for_newer_released_revs_list = list(
        trafo_revision_group_ids_to_check_for_newer_released_revs.keys()
    )

    newer_by_trafo_group_id = get_newest_released_trafo_rev(
        trafo_revision_group_ids_to_check_for_newer_released_revs_list,
        use_release_date=use_release_date,
    )

    current_revisions_for_draft_operators_by_trafo_id = get_current_revision_for_drafts(
        set(draft_trafo_ids)
    )

    updated_trafo = upgrade_operators_with_providided_revisions(
        trafo,
        newer_by_trafo_group_id,
        current_revisions_for_draft_operators_by_trafo_id,
        only_check_deprecated=only_check_deprecated,
        same_revision_no_op=same_revision_no_op,
    )

    return updated_trafo
