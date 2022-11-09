import re
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, root_validator, validator

from hetdesrun.datatypes import DataType
from hetdesrun.models.util import names_unique
from hetdesrun.models.workflow import ComponentNode, WorkflowNode
from hetdesrun.persistence.models.io import Connector, Constant, IOConnector
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.operator import NonEmptyValidStr, Operator


def get_link_start_connector_from_operator(
    link_start_operator_id: Optional[UUID],
    link_start_connector_id: UUID,
    operators: List[Operator],
) -> Optional[Connector]:

    for operator in operators:
        if operator.id == link_start_operator_id:
            for connector in operator.outputs:
                if connector.id == link_start_connector_id:
                    return connector

    return None


def get_link_end_connector_from_operator(
    link_end_operator_id: Optional[UUID],
    link_end_connector_id: UUID,
    operators: List[Operator],
) -> Optional[Connector]:

    for operator in operators:
        if operator.id == link_end_operator_id:
            for connector in operator.inputs:
                if connector.id == link_end_connector_id:
                    return connector

    return None


def get_link_by_output_connector(
    operator_id: Optional[UUID], connector_id: UUID, links: List[Link]
) -> Optional[Link]:

    for link in links:
        if (
            link.start.operator == operator_id
            and link.start.connector.id == connector_id
        ):
            return link

    return None


def get_link_by_input_connector(
    operator_id: Optional[UUID], connector_id: UUID, links: List[Link]
) -> Optional[Link]:
    for link in links:
        if link.end.operator == operator_id and link.end.connector.id == connector_id:
            return link

    return None


def get_input_by_link_start(
    link_start_connector_id: UUID,
    inputs: List[IOConnector],
) -> Optional[IOConnector]:

    for input_connector in inputs:
        if input_connector.id == link_start_connector_id:
            return input_connector

    return None


def get_constant_by_link_start(
    link_start_connector_id: UUID,
    constants: List[Constant],
) -> Optional[Constant]:

    for constant in constants:
        if constant.id == link_start_connector_id:
            return constant

    return None


def get_output_by_link_end(
    link_end_connector_id: UUID,
    outputs: List[IOConnector],
) -> Optional[IOConnector]:

    for output_connector in outputs:
        if output_connector.id == link_end_connector_id:
            return output_connector

    return None


class WorkflowContent(BaseModel):
    operators: List[Operator] = []
    links: List[Link] = Field([], description="Links may not form loops.")
    inputs: List[IOConnector] = Field(
        [],
        description=(
            "Workflow inputs are determined by operator inputs, "
            "which are not connected to links. "
            "If input names are set they must be unique."
        ),
    )
    outputs: List[IOConnector] = Field(
        [],
        description=(
            "Workflow outputs are determined by operator outputs, "
            "which are not connected to links. "
            "If output names are set they must be unique."
        ),
    )
    constants: List[Constant] = Field(
        [],
        description=(
            "Constant input values for the workflow are created "
            "by setting a workflow input to a fixed value."
        ),
    )

    # pylint: disable=no-self-argument
    @validator("operators", each_item=False)
    def operator_names_unique(cls, operators: List[Operator]) -> List[Operator]:
        operator_groups: dict[str, List[Operator]] = {}

        for operator in operators:
            operator_name_seed = re.sub(r" \([0-9]+\)$", "", operator.name)
            if operator_name_seed not in operator_groups:
                operator_groups[operator_name_seed] = [operator]
            else:
                operator_groups[operator_name_seed].append(operator)

        for operator_name_seed, operator_group in operator_groups.items():
            if len(operator_group) > 1:
                for index, operator in enumerate(operator_group):
                    if index == 0:
                        operator.name = NonEmptyValidStr(operator_name_seed)
                    else:
                        operator.name = NonEmptyValidStr(
                            operator_name_seed + " (" + str(index + 1) + ")"
                        )

        return operators

    # pylint: disable=no-self-argument
    @validator("links", each_item=False)
    def reduce_to_valid_links(cls, links: List[Link], values: dict) -> List[Link]:

        try:
            operators = values["operators"]
        except KeyError as e:
            raise ValueError(
                "Cannot reduce to valid links if attribute 'operators' is missing"
            ) from e

        updated_links: List[Link] = []

        for link in links:
            if link.start.operator is None or link.end.operator is None:
                # links from/to inputs/outputs will be dealt with in the clean_up_io_links validator
                updated_links.append(link)
            else:
                link_start_connector = get_link_start_connector_from_operator(
                    link.start.operator, link.start.connector.id, operators
                )
                link_end_connector = get_link_end_connector_from_operator(
                    link.end.operator, link.end.connector.id, operators
                )
                if (
                    link_start_connector is not None
                    and link_end_connector is not None
                    and (
                        link_start_connector.data_type == link_end_connector.data_type
                        or link_start_connector.data_type == DataType.Any
                        or link_end_connector.data_type == DataType.Any
                    )
                ):
                    link.start.connector = link_start_connector
                    link.end.connector = link_end_connector
                    updated_links.append(link)

        return updated_links

    # pylint: disable=no-self-argument
    @validator("links", each_item=False)
    def links_acyclic_directed_graph(cls, links: List[Link]) -> List[Link]:

        indegrees: Dict[UUID, int] = {}
        edges: List[Tuple[UUID, UUID]] = []

        def add_edge(edge: Tuple[UUID, UUID]) -> None:
            edges.append(edge)
            start_vertex = edge[0]
            end_vertex = edge[1]
            if start_vertex not in indegrees:
                indegrees[start_vertex] = 0
            if end_vertex not in indegrees:
                indegrees[end_vertex] = 1
            else:
                indegrees[end_vertex] = indegrees[end_vertex] + 1

        def remove_outgoing_edges(start_vertex: UUID) -> None:
            remove_edges: List[Tuple[UUID, UUID]] = []
            for edge in edges:
                if edge[0] == start_vertex:
                    if indegrees[edge[1]] > 0:
                        indegrees[edge[1]] = indegrees[edge[1]] - 1
                    remove_edges.append(edge)
            del indegrees[start_vertex]

            for edge in remove_edges:
                edges.remove(edge)

        def vertices_with_indegree_zero() -> List[UUID]:
            return [vertex for vertex, indegree in indegrees.items() if indegree == 0]

        for link in links:
            start_operator = link.start.operator
            end_operator = link.end.operator
            if start_operator is None:
                start_operator = link.start.connector.id
            if end_operator is None:
                end_operator = link.end.connector.id
            add_edge((start_operator, end_operator))

        while len(vertices_with_indegree_zero()) > 0:
            vertex = vertices_with_indegree_zero()[0]
            remove_outgoing_edges(vertex)

        if len(edges) > 0:
            raise ValueError("Links may not form any loop!")

        return links

    # pylint: disable=no-self-argument
    @validator("inputs", each_item=False)
    def determine_inputs_from_operators_and_links(
        cls, inputs: List[IOConnector], values: dict
    ) -> List[IOConnector]:

        try:
            operators = values["operators"]
            links = values["links"]
        except KeyError as e:
            raise ValueError(
                "Cannot determine inputs if any of the attributes 'operators', 'links' is missing"
            ) from e

        updated_inputs = []

        for operator in operators:
            for connector in operator.inputs:
                link = get_link_by_input_connector(operator.id, connector.id, links)
                if link is None:
                    updated_inputs.append(
                        IOConnector(
                            data_type=connector.data_type,
                            operator_id=operator.id,
                            connector_id=connector.id,
                            operator_name=operator.name,
                            connector_name=connector.name,
                        )
                    )
                else:
                    input_connector = get_input_by_link_start(
                        link.start.connector.id, inputs
                    )
                    if input_connector is not None:
                        updated_inputs.append(input_connector)

        return updated_inputs

    # pylint: disable=no-self-argument
    @validator("outputs", each_item=False)
    def determine_outputs_from_operators_and_links(
        cls, outputs: List[IOConnector], values: dict
    ) -> List[IOConnector]:

        try:
            operators = values["operators"]
            links = values["links"]
        except KeyError as e:
            raise ValueError(
                "Cannot determine outputs if any of the attributes 'operators', 'links' is missing"
            ) from e

        updated_outputs = []

        for operator in operators:
            for connector in operator.outputs:
                link = get_link_by_output_connector(operator.id, connector.id, links)
                if link is None:
                    updated_outputs.append(
                        IOConnector(
                            data_type=connector.data_type,
                            operator_id=operator.id,
                            connector_id=connector.id,
                            operator_name=operator.name,
                            connector_name=connector.name,
                        )
                    )
                else:
                    output_connector = get_output_by_link_end(
                        link.end.connector.id, outputs
                    )
                    if output_connector is not None:
                        updated_outputs.append(output_connector)

        return updated_outputs

    # pylint: disable=no-self-argument
    @validator("inputs", "outputs", each_item=False)
    def connector_names_empty_or_unique(
        cls, io_connectors: List[IOConnector]
    ) -> List[IOConnector]:

        io_connectors_with_nonempty_name = [
            io_connector
            for io_connector in io_connectors
            if not (io_connector.name is None or io_connector.name == "")
        ]

        names_unique(cls, io_connectors_with_nonempty_name)

        return io_connectors

    @root_validator()
    def clean_up_io_links(cls, values: dict) -> dict:

        try:
            operators = values["operators"]
            links = values["links"]
            constants = values["constants"]
            inputs = values["inputs"]
            outputs = values["outputs"]
        except KeyError as e:
            raise ValueError(
                "Cannot clean up io links if any of the attributes "
                "'operators', 'links', 'constants', 'inputs' and 'outputs' is missing"
            ) from e

        updated_links: List[Link] = []

        for link in links:
            if not (link.start.operator is None or link.end.operator is None):
                # link has been checked in the reduce_to_valid_links validator already
                updated_links.append(link)
            elif link.start.operator is None:
                input_connector = get_input_by_link_start(
                    link.start.connector.id, inputs
                )
                if not (input_connector is None or input_connector.name == ""):
                    link_end_connector = get_link_end_connector_from_operator(
                        link.end.operator, link.end.connector.id, operators
                    )
                    if link_end_connector is not None and (
                        input_connector.data_type == link_end_connector.data_type
                        or input_connector.data_type == DataType.Any
                        or link_end_connector.data_type == DataType.Any
                    ):
                        link.start.connector = input_connector.to_connector()
                        link.end.connector = link_end_connector
                        updated_links.append(link)
                constant = get_constant_by_link_start(
                    link.start.connector.id, constants
                )
                if not constant is None:
                    link_end_connector = get_link_end_connector_from_operator(
                        link.end.operator, link.end.connector.id, operators
                    )
                    if link_end_connector is not None and (
                        constant.data_type == link_end_connector.data_type
                        or constant.data_type == DataType.Any
                        or link_end_connector.data_type == DataType.Any
                    ):
                        link.start.connector = constant.to_connector()
                        link.end.connector = link_end_connector
                        updated_links.append(link)
            else:  # link.end.operator is None:
                output_connector = get_output_by_link_end(
                    link.end.connector.id, outputs
                )
                if not (output_connector is None or output_connector.name == ""):
                    link_start_connector = get_link_start_connector_from_operator(
                        link.start.operator, link.start.connector.id, operators
                    )
                    if link_start_connector is not None and (
                        link_start_connector.data_type == output_connector.data_type
                        or link_start_connector.data_type == DataType.Any
                        or output_connector.data_type == DataType.Any
                    ):
                        link.start.connector = link_start_connector
                        link.end.connector = output_connector.to_connector()
                        updated_links.append(link)

        # frontend sends link in put-request if input/output is named
        # -> no need to create links

        values["links"] = updated_links

        return values

    def to_workflow_node(
        self,
        operator_id: Optional[UUID],
        name: Optional[str],
        sub_nodes: List[Union[WorkflowNode, ComponentNode]],
    ) -> WorkflowNode:

        inputs = []
        for input_connector in self.inputs:
            link = get_link_by_output_connector(None, input_connector.id, self.links)
            if link is not None and link.end.connector.name is not None:
                assert link.end.operator is not None
                # input must be connected to some operator
                inputs.append(
                    input_connector.to_workflow_input(
                        link.end.operator, link.end.connector.name
                    )
                )
        for constant in self.constants:
            cn_constant = constant.to_connector()
            link = get_link_by_output_connector(None, cn_constant.id, self.links)
            if link is not None and link.end.connector.name is not None:
                assert link.end.operator is not None
                # constant must be connected to some operator
                inputs.append(
                    constant.to_workflow_input(
                        link.end.operator, link.end.connector.name
                    )
                )

        outputs = []
        for output_connector in self.outputs:
            link = get_link_by_input_connector(None, output_connector.id, self.links)
            if link is not None and link.start.connector.name is not None:
                assert link.start.operator is not None
                # output must be connected to some operator
                outputs.append(
                    output_connector.to_workflow_output(
                        link.start.operator, link.start.connector.name
                    )
                )

        return WorkflowNode(
            id=str(operator_id),
            sub_nodes=sub_nodes,
            connections=[
                link.to_connection()
                for link in self.links
                # only inner links are relevant connections
                if not (link.start.operator is None or link.end.operator is None)
            ],
            inputs=inputs,
            outputs=outputs,
            name=name,
        )

    class Config:
        validate_assignment = True
