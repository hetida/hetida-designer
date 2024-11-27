from collections.abc import Callable, Coroutine
from inspect import Parameter, signature
from typing import Any, Protocol

from asyncstdlib.functools import cached_property  # async compatible variant
from pydantic import ValidationError

from hetdesrun.datatypes import NamedDataTypedValue, parse_dynamically_from_datatypes
from hetdesrun.models.run import HIERARCHY_SEPARATOR
from hetdesrun.runtime import runtime_execution_logger
from hetdesrun.runtime.configuration import execution_config
from hetdesrun.runtime.context import ExecutionContext
from hetdesrun.runtime.engine.plain.execution import run_func_or_coroutine
from hetdesrun.runtime.exceptions import (
    CircularDependency,
    ComponentException,
    MissingInputSource,
    MissingOutputException,
    RuntimeExecutionError,
    UnexpectedComponentException,
    WorkflowInputDataValidationError,
)
from hetdesrun.runtime.logging import execution_context_filter
from hetdesrun.utils import Type

runtime_execution_logger.addFilter(execution_context_filter)


class Node(Protocol):
    """Protocol for common structural type features for workflow (sub)nodes"""

    # Note: The result attribute should be defined to be a cached_property in actual implementations
    # to avoid recomputing the result several times when values are accessed as inputs for more than
    # one other node.

    _in_computation: bool = False
    has_only_plot_outputs: bool = False
    operator_hierarchical_id: str = "UNKNOWN"
    operator_hierarchical_name: str = "UNKNOWN"
    context: ExecutionContext

    @cached_property
    async def result(self) -> dict[str, Any]:  # Outputs can have any type
        ...

    def add_inputs(self, new_inputs: dict[str, tuple["Node", str]]) -> None: ...


class ComputationNode:
    """Represents a function computation with multiple outputs together with input information

    Inputs and outputs are not made explicit here and the information where the inputs
    come from does not need to be complete at initialization time. To add input information later
    use the add_inputs method. Completeness of input is checked when starting a function computation
    and incomplete input information then leads to an appropriate exception.

    Which inputs are actually required depends implicitely on the actual function. This allows
    the function to have true optional (keyword) arguments.

    The result is a cached property such that computation only runs once during the node's lifetime.
    The computation collects result from other computation nodes result properties and therefore may
    trigger a self-organizing computation graph execution.

    Circular dependencies are detected during computation and an appropriate exception is raised.
    """

    def __init__(
        self,
        func: Coroutine | Callable,
        inputs: dict[str, tuple[Node, str]] | None = None,
        has_only_plot_outputs: bool = False,
        component_id: str = "UNKNOWN",
        component_name: str = "UNKNOWN",
        component_tag: str = "UNKNOWN",
        operator_hierarchical_id: str = "UNKNOWN",
        operator_hierarchical_name: str = "UNKNOWN",
    ) -> None:
        """
        inputs is a dict {input_name : (another_node, output_name)}, i.e. mapping input names to
        pairs (another_node, output_name). Inputs do not need to be provided at initialization.

        func is a function or coroutine function with the input_names as keyword arguments. It
        should output a dict of result values.

        operator_hierarchical_id, component_id, operator_hierarchical_name and component_name can be
        provided to enrich logging and exception messages.

        The computation node inputs may or may not be complete, i.e. all required inputs are given
        or not. If not complete, computation of result may simply fail, e.g. with
            TypeError: <lambda>() missing 1 required positional argument: 'base_value'
        or
            TypeError: f() missing 1 required keyword-only argument: 'base_value'

        However the availability of all inputs is checked during execution by inspecting the
        provided func and comparing to currently set inputs. MissingInputSource exception is
        raised if inputs are missing.

        """
        self.inputs: dict[str, tuple[Node, str]] = {}
        if inputs is not None:
            self.add_inputs(inputs)

        self.func = func

        self.required_params = self._infer_required_params()

        self._in_computation = False  # to detect cycles

        self.has_only_plot_outputs = has_only_plot_outputs
        self.operator_hierarchical_id = operator_hierarchical_id
        self.operator_hierarchical_name = operator_hierarchical_name
        self.context = ExecutionContext(
            currently_executed_transformation_id=component_id,
            currently_executed_transformation_name=component_name
            if component_name is not None
            else "UNKNOWN",
            currently_executed_transformation_tag=component_tag,
            currently_executed_transformation_type=Type.COMPONENT,
            currently_executed_operator_hierarchical_id=self.operator_hierarchical_id,
            currently_executed_operator_hierarchical_name=self.operator_hierarchical_name,
        )
        self._in_computation = False

    def add_inputs(self, new_inputs: dict[str, tuple[Node, str]]) -> None:
        self.inputs.update(new_inputs)

    def _infer_required_params(self) -> list[str]:
        """Infer the function params which are actually required (i.e. no default value)"""
        kwargable_params = [
            param
            for param in signature(self.func).parameters.values()  # type: ignore
            if (param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY))
        ]
        # only non-default-valued params are required:
        return [param.name for param in kwargable_params if param.default is Parameter.empty]

    def all_required_inputs_set(self) -> bool:
        return set(self.required_params).issubset(set(self.inputs.keys()))

    def _check_inputs(self) -> None:
        """Check and handle missing inputs"""
        if not self.all_required_inputs_set():
            runtime_execution_logger.warning(
                "Computation node execution failed due to missing input source"
            )
            raise MissingInputSource(
                f"Inputs of computation node are missing."
                f" Provided inputs are: {str(set(self.inputs.keys()))}."
                f" Required params are: {str(set(self.required_params))}."
            ).set_context(self.context)

    async def _gather_data_from_inputs(self) -> dict[str, Any]:
        """Get data from inputs and handle possible cycles"""

        input_value_dict: dict[str, Any] = {}

        for input_name, (another_node, output_name) in self.inputs.items():
            # Cycle detection logic
            if another_node._in_computation:
                msg = (
                    f"Circular Dependency detected whith input '{input_name}' pointing to "
                    f"output '{output_name}' of operator {another_node.operator_hierarchical_id}"
                )
                runtime_execution_logger.warning(msg)
                raise CircularDependency(msg).set_context(self.context)
            # actually get input data from other nodes
            try:
                input_value_dict[input_name] = (await another_node.result)[output_name]
            except KeyError as exc:
                # possibly an output_name missing in the result dict of one of the providing nodes!
                runtime_execution_logger.warning(
                    "Execution failed due to missing output of a node",
                    exc_info=True,
                )
                raise MissingOutputException(
                    "Could not obtain output result from another node while preparing to "
                    "run operator"
                ).set_context(self.context) from exc
        return input_value_dict

    async def _run_comp_func(self, input_values: dict[str, Any]) -> dict[str, Any]:
        """Running the component func with exception handling"""
        try:
            function_result: dict[str, Any] = await run_func_or_coroutine(
                self.func,  # type: ignore
                input_values,
            )
            function_result = function_result if function_result is not None else {}
        except Exception as exc:  # uncaught exceptions from user code  # noqa: BLE001
            if hasattr(exc, "__is_hetida_designer_exception__") and hasattr(exc, "error_code"):
                runtime_execution_logger.warning(
                    "User raised a hetida designer exception in component code.",
                    exc_info=True,
                )
                raise ComponentException(
                    exc,
                    error_code=exc.error_code,
                    extra_information=exc.extra_information
                    if hasattr(exc, "extra_information")
                    else None,
                ).set_context(self.context) from exc
            msg = "Unexpected error from user code."
            runtime_execution_logger.warning(msg, exc_info=True)
            raise UnexpectedComponentException(msg).set_context(self.context) from exc

        if not isinstance(
            function_result, dict
        ):  # user functions may return completely unknown type
            msg = "Component did not return an output dict."
            runtime_execution_logger.warning(msg, exc_info=True)
            raise RuntimeExecutionError(msg).set_context(self.context)

        return function_result

    async def _compute_result(self) -> dict[str, Any]:
        # set filter for contextualized logging
        execution_context_filter.bind_context(**self.context.dict())

        runtime_execution_logger.info("Starting computation")
        self._in_computation = True

        self._check_inputs()

        # Gather data from input sources (detects cycles):
        input_values = await self._gather_data_from_inputs()

        # Actual execution of current node
        function_result = await self._run_comp_func(input_values)

        # cleanup
        self._in_computation = False
        execution_context_filter.clear_context()

        return function_result

    @cached_property  # compute each nodes result only once
    async def result(self) -> dict[str, Any]:
        return await self._compute_result()


class Workflow:
    """Grouping computation nodes and other workflows and handling common input/output interface

    This class does not ensure that the interface actually handles all lose ends.
    """

    def __init__(
        self,
        sub_nodes: list[Node],
        input_mappings: dict[str, tuple[Node, str]],  # map wf input to sub_node
        output_mappings: dict[str, tuple[Node, str]],  # map sub_node outputs to wf outputs
        tr_id: str,
        tr_name: str,
        tr_tag: str,
        inputs: dict[str, tuple[Node, str]] | None = None,
        has_only_plot_outputs: bool = False,
        operator_hierarchical_id: str = "UNKNOWN",
        operator_hierarchical_name: str = "UNKNOWN",
    ):
        """Initialize new Workflow

        Args:
            sub_nodes (List[Node]): The sub nodes of this Workflow. Workflows can have workflows
                as subnodes.
            input_mappings (Dict[str, Tuple[Node, str]]): How inputs of the workflow are mapped
                to inputs of sub nodes. Maps the workflow input name to a pair consisting of a
                Node (which should be subnode) and the name of an input of that node.
            output_mappings (Dict[str, Tuple[Node, str]]): How outputs of sub nodes are mapped
                to workflow outputs. Maps the workflow output name to a pair consisting of a
                Node (which should be a subnode) and the name of an output of that node.
            inputs: Optional[Dict[str, Tuple[Node, str]]]: Inputs which this workflow gets from
                outputs of other Nodes (possibly outside the workflow). This is for example used
                for workflows that are sub nodes of workflows. This does not need to be provided
                at initialization -- the add_inputs method may be used instead at a later point.
                Therefore defaults to None.
            operator_hierarchical_id (str, optional): Used in logging and exception messages.
                Defaults to "UNKNOWN".
            operator_name (str, optional): Used in logging and exception messages. Defaults to
                "UNKNOWN".
        """
        self.sub_nodes = sub_nodes
        self.input_mappings = input_mappings  # dict wf_input_name : (sub_node, sub_node_input_name)
        self.output_mappings = (
            output_mappings  # dict wf_output_name : (sub_node, sub_node_output_name)
        )

        self.inputs: dict[str, tuple[Node, str]] = {}

        if inputs is not None:
            self.add_inputs(inputs)

        self._in_computation: bool = False
        self.has_only_plot_outputs = has_only_plot_outputs
        self.operator_hierarchical_id = operator_hierarchical_id
        self.operator_hierarchical_name = operator_hierarchical_name

        self.context = ExecutionContext(
            currently_executed_transformation_id=tr_id,
            currently_executed_transformation_name=tr_name,
            currently_executed_transformation_tag=tr_tag,
            currently_executed_transformation_type=Type.WORKFLOW,
            currently_executed_operator_hierarchical_id=self.operator_hierarchical_id,
            currently_executed_operator_hierarchical_name=self.operator_hierarchical_name,
        )

    def add_inputs(self, new_inputs: dict[str, tuple[Node, str]]) -> None:
        self.inputs.update(new_inputs)

        # wire them to the subnodes, eventually overwriting existing wirings
        for key, (another_node, output_name) in new_inputs.items():
            sub_node, sub_node_input_name = self.input_mappings[key]
            sub_node.add_inputs({sub_node_input_name: (another_node, output_name)})

    def add_constant_providing_node(
        self,
        values: list[NamedDataTypedValue],
        optional: bool = False,
        add_new_provider_node_to_workflow: bool = True,
        id_suffix: str = "",
    ) -> None:
        """Add a node with no inputs providing workflow input data"""
        try:
            parsed_values = parse_dynamically_from_datatypes(values, optional).dict()
        except ValidationError as e:
            raise WorkflowInputDataValidationError(
                "The provided data or some constant or default values could not be parsed into the "
                "respective workflow input datatypes."
            ).set_context(self.context) from e

        Const_Node = ComputationNode(
            func=lambda: parsed_values,
            inputs={},
            operator_hierarchical_name=self.operator_hierarchical_name
            + "constant_provider_"
            + id_suffix
            + HIERARCHY_SEPARATOR,
            operator_hierarchical_id=self.operator_hierarchical_id + "" + HIERARCHY_SEPARATOR,
        )
        if add_new_provider_node_to_workflow:  # make it part of the workflow
            self.sub_nodes.append(Const_Node)
        self.add_inputs({key: (Const_Node, key) for key in parsed_values})

    def _wire_workflow_inputs(self) -> None:
        """Wire the current inputs via the current input mappings to the appropriate sub nodes"""
        for (
            wf_inp_name,
            (sub_node, sub_node_input_name),
        ) in self.input_mappings.items():
            try:
                sub_node.add_inputs({sub_node_input_name: self.inputs[wf_inp_name]})
            except KeyError as error:
                inputs_string = "', '".join(self.inputs.keys())
                raise MissingInputSource(
                    f"The input mapping with workflow input '{wf_inp_name}' to "
                    f"subnode input '{sub_node_input_name}' of "
                    f"subnode '{sub_node.operator_hierarchical_id}' "
                    f"does not match the inputs of the workflow '{inputs_string}'."
                ).set_context(self.context) from error

    @cached_property
    async def result(self) -> dict[str, Any]:
        self._wire_workflow_inputs()

        execution_context_filter.bind_context(**self.context.dict())

        runtime_execution_logger.info("Starting computation")

        # gather result from workflow operators
        results = {}
        exe_context_config = execution_config.get()

        for (
            wf_output_name,
            (
                sub_node,
                sub_node_output_name,
            ),
        ) in self.output_mappings.items():
            try:
                results[wf_output_name] = (
                    (await sub_node.result)[sub_node_output_name]
                    if not (
                        sub_node.has_only_plot_outputs is True
                        and exe_context_config.run_pure_plot_operators is False
                    )
                    else {}
                )
            except KeyError as e:
                # possibly an output_name missing in the result dict of one of the providing nodes!
                msg = (
                    f"Declared output '{sub_node_output_name}' "
                    "not contained in returned dictionary."
                )
                runtime_execution_logger.warning(msg, exc_info=True)
                raise MissingOutputException(msg).set_context(sub_node.context) from e
            except RuntimeExecutionError as e:
                raise e

        # cleanup
        execution_context_filter.clear_context()

        return results


def obtain_all_nodes(wf: Workflow) -> list[ComputationNode]:
    all_nodes: list[ComputationNode] = []
    for node in wf.sub_nodes:
        if isinstance(node, Workflow):
            all_nodes = all_nodes + obtain_all_nodes(node)
        else:
            assert isinstance(node, ComputationNode)  # hint for mypy  # noqa: S101
            all_nodes.append(node)
    return all_nodes
