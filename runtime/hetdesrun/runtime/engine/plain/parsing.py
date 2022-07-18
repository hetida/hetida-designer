"""Parse workflow input into data structures of plain engine"""
import logging
from typing import Callable, Coroutine, Dict, List, Tuple, Union, cast

from hetdesrun.component.load import ComponentCodeImportError, import_func_from_code
from hetdesrun.datatypes import DataType, NamedDataTypedValue
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentOutput, ComponentRevision
from hetdesrun.models.workflow import (
    ComponentNode,
    WorkflowConnection,
    WorkflowInput,
    WorkflowNode,
    WorkflowOutput,
)
from hetdesrun.runtime.engine.plain.workflow import ComputationNode, Node, Workflow

logger = logging.getLogger(__name__)


class WorkflowParsingException(Exception):
    pass


class NodeFunctionLoadingError(WorkflowParsingException):
    pass


class NodeDoesNotExistError(WorkflowParsingException):
    pass


class ComponentRevisionDoesNotExist(WorkflowParsingException):
    pass


class ConnectionInvalidError(WorkflowParsingException):
    pass


def only_plot_outputs(
    outputs: Union[List[ComponentOutput], List[WorkflowOutput]]
) -> bool:
    # in case of an empty output list all will yield true
    return len(outputs) > 0 and all(
        output.type == DataType.PlotlyJson for output in outputs
    )


def parse_workflow_input(
    workflow_node: WorkflowNode,
    components: List[ComponentRevision],
    code_modules: List[CodeModule],
) -> Workflow:

    component_dict: Dict[str, ComponentRevision] = {str(c.uuid): c for c in components}

    code_module_dict: Dict[str, CodeModule] = {str(c.uuid): c for c in code_modules}

    workflow = recursively_parse_workflow_node(
        workflow_node, component_dict, code_module_dict, name_prefix="", id_prefix=""
    )

    return workflow


def load_func(
    component: ComponentRevision, code_module_dict: Dict[str, CodeModule]
) -> Union[Coroutine, Callable]:
    """Load entrypoint function"""
    code_module_uuid = component.code_module_uuid
    try:
        code = code_module_dict[str(code_module_uuid)].code
    except KeyError as e:
        # This could alternatively be efficiently validated upfront in WorkflowExecutionInput.
        # However we do it here to be consistent with the other checks (e.g. operators
        # refering existing component revisions) which require actual recursive parsing
        # of the complete workflow structure.
        msg = (
            f"The code module with UUID {str(code_module_uuid)} which was referenced by"
            f"component revision with UUID {component.uuid} was not provided"
        )
        logger.info(msg)
        raise NodeFunctionLoadingError(msg) from e

    try:
        component_func = import_func_from_code(
            code,
            component.function_name,
        )
    except (ImportError, ComponentCodeImportError) as e:
        msg = (
            f"Could not load node function (Code module uuid: "
            f"{component.code_module_uuid}, Component uuid: {component.uuid}, "
            f" function name: {component.function_name})"
        )
        logger.info(msg)
        raise NodeFunctionLoadingError(msg) from e
    return component_func


def parse_component_node(
    component_node: ComponentNode,
    component_dict: Dict[str, ComponentRevision],
    code_module_dict: Dict[str, CodeModule],
    name_prefix: str,
    id_prefix: str,
) -> ComputationNode:
    """Parse component node into a ComputationNode

    Includes importing and loading of component function
    """
    component_node_name = (
        component_node.name if component_node.name is not None else "UNKNOWN"
    )
    try:
        comp_rev = component_dict[component_node.component_uuid]
    except KeyError as e:
        msg = (
            f"The component revision with UUID {component_node.component_uuid} referenced in"
            f"the workflow in operator {str(component_node.name)} is not present in"
            " the provided components"
        )
        logger.info(msg)
        raise ComponentRevisionDoesNotExist(msg) from e

    # Load entrypoint function
    component_func = load_func(comp_rev, code_module_dict)

    return ComputationNode(
        func=component_func,
        component_id=component_node.component_uuid,
        operator_hierarchical_name=name_prefix + " : " + component_node_name
        if name_prefix != ""
        else component_node_name,
        inputs=None,  # inputs are added later by the surrounding workflow
        has_only_plot_outputs=only_plot_outputs(comp_rev.outputs),
        operator_hierarchical_id=id_prefix + " : " + component_node.id,
    )


def apply_connections(
    wf_sub_nodes: Dict[str, Node],
    connections: List[WorkflowConnection],
) -> None:
    """Wires one level of a workflow from this level's connections

    This manfests the internal wiring of the workflow, i.e. connections between
    its operators on the current level (i.e. not handling the internal wiring of sub workflows)
    """
    for conn in connections:
        try:
            referenced_source_node = wf_sub_nodes[conn.input_in_workflow_id]
        except KeyError as e:
            msg = (
                f"Referenced Source Node with UUID {conn.input_in_workflow_id} of a connection"
                " could not be found"
            )
            logger.info(msg)
            raise ConnectionInvalidError(msg) from e

        try:
            referenced_target_node = wf_sub_nodes[conn.output_in_workflow_id]
        except KeyError as e:
            msg = (
                f"Referenced Target Node with UUID {conn.output_in_workflow_id} of a connection"
                " could not be found"
            )
            logger.info(msg)
            raise ConnectionInvalidError(msg) from e

        referenced_target_node.add_inputs(
            {conn.output_name: (referenced_source_node, conn.input_name)}
        )


def obtain_inputs_by_role(
    node: WorkflowNode,
) -> Tuple[List[WorkflowInput], List[WorkflowInput]]:
    """
    returns a pair of Lists where the first list contains all dynamic inputs and the second
    consists of all constant inputs
    """
    wf_inputs = node.inputs
    dynamic_inputs = [inp for inp in wf_inputs if not inp.constant]
    constant_inputs = [inp for inp in wf_inputs if inp.constant]
    return (dynamic_inputs, constant_inputs)


def generate_constant_input_name(inp: WorkflowInput) -> str:
    return "generated_constant_input_" + inp.id_of_sub_node + "_" + inp.name_in_subnode


def obtain_mappings(
    dynamic_inputs: List[WorkflowInput],
    constant_inputs: List[WorkflowInput],
    outputs: List[WorkflowOutput],
    new_sub_nodes: Dict[str, Node],
) -> Tuple[
    Dict[str, Tuple[Node, str]],
    Dict[str, Tuple[Node, str]],
    Dict[str, Tuple[Node, str]],
]:
    """
    Return Tripel consisting of dynamic input mappings, constant input mappings, output mappings
    """
    dynamic_input_mappings: Dict[str, Tuple[Node, str]] = {
        cast(str, inp.name): (
            # casting since mypy does not know that for non-constant inputs
            # a name is mandatory
            new_sub_nodes[inp.id_of_sub_node],
            inp.name_in_subnode,
        )
        for inp in dynamic_inputs
    }

    constant_input_mappings = {
        generate_constant_input_name(inp): (
            new_sub_nodes[inp.id_of_sub_node],
            inp.name_in_subnode,
        )
        for inp in constant_inputs
    }

    output_mappings = {
        outp.name: (new_sub_nodes[outp.id_of_sub_node], outp.name_in_subnode)
        for outp in outputs
    }

    return (dynamic_input_mappings, constant_input_mappings, output_mappings)


def recursively_parse_workflow_node(
    node: WorkflowNode,
    component_dict: Dict[str, ComponentRevision],
    code_module_dict: Dict[str, CodeModule],
    name_prefix: str = "",
    id_prefix: str = "",
) -> Workflow:
    """Depth first recursive parsing of workflow nodes

    To simplify log analysis names and ids are set hierarchically (" : " seperated) for nested
    workflows.
    """
    node_name = node.name if node.name is not None else "UNKNOWN"
    new_sub_nodes: Dict[str, Node] = {}
    for sub_input_node in node.sub_nodes:
        new_sub_node: Node
        if isinstance(sub_input_node, WorkflowNode):
            new_sub_node = recursively_parse_workflow_node(
                sub_input_node,
                component_dict,
                code_module_dict,
                name_prefix=name_prefix + " : " + node_name
                if name_prefix != ""
                else node_name,
                id_prefix=id_prefix + " : " + node.id if id_prefix != "" else node.id,
            )
        else:  # ComponentNode
            assert isinstance(sub_input_node, ComponentNode)  # hint for mypy # nosec
            new_sub_node = parse_component_node(
                sub_input_node,
                component_dict,
                code_module_dict,
                name_prefix + " : " + node_name if name_prefix != "" else node_name,
                id_prefix + " : " + node.id if id_prefix != "" else node.id,
            )
        new_sub_nodes[str(sub_input_node.id)] = new_sub_node

    connections: List[WorkflowConnection] = node.connections

    apply_connections(new_sub_nodes, connections)

    # Obtain input and output mappings
    wf_outputs = node.outputs
    has_only_plot_outputs = only_plot_outputs(wf_outputs)

    dynamic_inputs, constant_inputs = obtain_inputs_by_role(node)

    dynamic_input_mappings, constant_input_mappings, output_mappings = obtain_mappings(
        dynamic_inputs, constant_inputs, wf_outputs, new_sub_nodes
    )

    input_mappings = {
        **dynamic_input_mappings,
        **constant_input_mappings,
    }  # generated constant input name: (subnode, subnode_inp_name)

    # Create workflow
    workflow = Workflow(
        sub_nodes=list(new_sub_nodes.values()),
        input_mappings=input_mappings,
        output_mappings=output_mappings,
        has_only_plot_outputs=has_only_plot_outputs,
        operator_hierarchical_id=id_prefix + " : " + node.id,
        operator_hierarchical_name=name_prefix + " : " + node_name
        if name_prefix != ""
        else node_name,
    )

    # provide constant data
    workflow.add_constant_providing_node(
        values=[
            NamedDataTypedValue(
                name=generate_constant_input_name(inp),
                type=inp.type,
                value=inp.constantValue["value"],
            )
            for inp in constant_inputs
        ],
        id_suffix="workflow_constant_values",
    )

    return workflow
