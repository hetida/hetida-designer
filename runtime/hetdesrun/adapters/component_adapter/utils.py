from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError

from hdutils import DataType
from hetdesrun.adapters.generic_rest.external_types import ExternalType
from hetdesrun.backend.execution import TrafoExecutionInputValidationError, nested_nodes
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentInput, ComponentRevision
from hetdesrun.models.data_selection import FilteredSink, FilteredSource
from hetdesrun.models.run import ConfigurationInput, WorkflowExecutionInput
from hetdesrun.models.wiring import InputWiring, WorkflowWiring
from hetdesrun.persistence.models.io import (
    InputType,
    IOInterface,
    TransformationInput,
    TransformationOutput,
)
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type

# need DataType (component output) to ExternalType mapping

data_type_to_external_type_map = {
    DataType.Integer: ExternalType.METADATA_INT,
    DataType.Float: ExternalType.METADATA_FLOAT,
    DataType.String: ExternalType.METADATA_STR,
    DataType.DataFrame: ExternalType.DATAFRAME,
    DataType.Series: ExternalType.TIMESERIES_NUMERIC,
    DataType.MultiTSFrame: ExternalType.MULTITSFRAME,
    DataType.Boolean: ExternalType.METADATA_BOOLEAN,
    DataType.Any: ExternalType.METADATA_ANY,
    DataType.PlotlyJson: ExternalType.PLOTLYJSON,
}


def workflow_wiring_from_source_filters(
    filtered_source: FilteredSource, component_rev_inputs_by_name: dict[str, ComponentInput]
) -> WorkflowWiring:
    """Converts the filters from a component adapter source to a wiring

    This wiring can then be used to run the referenced component.
    """
    return WorkflowWiring(
        input_wirings=[
            InputWiring(
                workflow_input_name=filter_key,
                adapter_id="direct_provisioning",
                filters={"value": filter_val},
                type=data_type_to_external_type_map[component_rev_inputs_by_name[filter_key].type],
            )
            for filter_key, filter_val in filtered_source.filters.items()
        ],
        # unwired outputs default to direct_provisioning, so we do not need to set this here:
        output_wirings=[],
    )


def workflow_wiring_from_sink_filters(
    filtered_sink: FilteredSink, value: Any, component_rev_inputs_by_name: dict[str, ComponentInput]
) -> WorkflowWiring:
    """Converts the filters from a component adapter source to a wiring

    This wiring can then be used to run the referenced component.
    """
    return WorkflowWiring(
        input_wirings=(
            [
                InputWiring(
                    workflow_input_name=filter_key,
                    adapter_id="direct_provisioning",
                    filters={"value": filter_val},
                    type=data_type_to_external_type_map[
                        component_rev_inputs_by_name[filter_key].type
                    ],
                )
                for filter_key, filter_val in filtered_sink.filters.items()
            ]
            + [
                InputWiring(
                    workflow_input_name="data",
                    adapter_id="direct_provisioning",
                    filters={"value": value},
                    type=filtered_sink.type,  # filtered_sink.type is a string rep of ExternalType
                )
            ]
        ),
        # unwired outputs default to direct_provisioning, so we do not need to set this here:
        output_wirings=[],
    )


def to_component_trafo_rev(
    component_revision: ComponentRevision, code_module: CodeModule
) -> TransformationRevision:
    """Reconstruct a trafo rev from component rev and code module

    This function recreates a TransformationRevision (stub with some info missing) from
    the ComponentRevision and CodeModule.

    The runtime does never get transformation revisions but only broken down
    stuff that only contain what is necessary to execute them.

    For the component adapter in the runtime, in order to handle proper wrapping as workflow
    and things that prepare_execution_input normally does in the backend, we need a
    TransformationRevision object to reuse the respective steps.
    """
    return TransformationRevision(
        id=component_revision.uuid,
        revision_group_id=UUID(
            "00000000-1111-0000-1111-000000000000"
        ),  # unfortunately we don't have that info.
        # Therefore we use a fixed (obviously wrong) uuid here for revision_group_id
        name=component_revision.name,
        description=(
            "TRAFO REV "
            + (component_revision.name if component_revision.name is not None else "UNKNOWN_NAME")
            + " ("
            + component_revision.tag
            + ") "
            + " REGENERATED FOR COMPONENT ADAPTER"
        ),
        category="UNKNOWN CATEGORY SINCE REGENERATED FOR COMPONENT ADAPTER",
        version_tag=component_revision.tag,
        disabled_timestamp=None,
        released_timestamp=None,
        state=State.DRAFT,
        type=Type.COMPONENT,
        documentation="UNKNOWN DOCUMENTATION SINCE REGENERATED FOR COMPONENT ADAPTER",
        content=code_module.code,
        io_interface=IOInterface(
            inputs=[
                TransformationInput(
                    id=comp_inp.id,
                    name=comp_inp.name,
                    data_type=comp_inp.type,
                    type=(InputType.OPTIONAL if comp_inp.default else InputType.REQUIRED),
                    value=comp_inp.default_value,
                )
                for comp_inp in component_revision.inputs
            ],
            outputs=[
                TransformationOutput(
                    id=comp_outp.id,
                    name=comp_outp.name,
                    data_type=comp_outp.type,
                )
                for comp_outp in component_revision.outputs
            ],
        ),
        test_wiring=WorkflowWiring(),
        release_wiring=None,
    )


def wf_exec_input_from_component_trafo_revision(
    component_trafo_rev: TransformationRevision,
    wiring: WorkflowWiring | None,
    run_pure_plot_operators: bool = True,
    job_id: UUID | None = None,
) -> WorkflowExecutionInput:
    tr_workflow = component_trafo_rev.wrap_component_in_tr_workflow()
    assert isinstance(  # noqa: S101
        tr_workflow.content, WorkflowContent
    )  # hint for mypy

    nested_transformations = {tr_workflow.content.operators[0].id: component_trafo_rev}
    nested_components = {
        tr.id: tr for tr in nested_transformations.values() if tr.type == Type.COMPONENT
    }

    workflow_node = tr_workflow.to_workflow_node(
        operator_id=uuid4(),
        sub_nodes=nested_nodes(tr_workflow, nested_transformations),
    )

    try:
        execution_input = WorkflowExecutionInput(
            code_modules=(
                [tr_component.to_code_module() for tr_component in nested_components.values()]
            ),
            components=(
                [component.to_component_revision() for component in nested_components.values()]
            ),
            workflow=workflow_node,
            configuration=ConfigurationInput(
                name=str(tr_workflow.id),
                run_pure_plot_operators=run_pure_plot_operators,
            ),
            workflow_wiring=wiring if wiring is not None else component_trafo_rev.test_wiring,
            job_id=uuid4() if job_id is None else job_id,
            trafo_id=component_trafo_rev.id,
        )
    except ValidationError as e:
        raise TrafoExecutionInputValidationError(e) from e

    return execution_input
