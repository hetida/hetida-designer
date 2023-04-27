import logging
import re
from uuid import UUID

from pydantic import BaseModel, Field, root_validator, validator

from hetdesrun.models.util import names_unique
from hetdesrun.models.workflow import ComponentNode, WorkflowNode
from hetdesrun.persistence.models.io import (
    OperatorInput,
    OperatorOutput,
    WorkflowContentConstantInput,
    WorkflowContentDynamicInput,
    WorkflowContentIO,
    WorkflowContentOutput,
)
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.operator import NonEmptyValidStr, Operator

logger = logging.getLogger(__name__)


# TODO: replace by operator_output_by_id_tuple_dict
def get_link_start_connector_from_operator(
    link_start_operator_id: UUID | None,
    link_start_connector_id: UUID,
    operators: list[Operator],
    # ) -> Connector | None:
) -> OperatorOutput | None:
    for operator in operators:
        if operator.id == link_start_operator_id:
            for opterator_output in operator.outputs:
                if opterator_output.id == link_start_connector_id:
                    return opterator_output

    return None


# TODO: replace by operator_input_by_id_tuple_dict
def get_link_end_connector_from_operator(
    link_end_operator_id: UUID | None,
    link_end_connector_id: UUID,
    operators: list[Operator],
    # ) -> Connector | None:
) -> OperatorInput | None:
    for operator in operators:
        if operator.id == link_end_operator_id:
            for operator_input in operator.inputs:
                if operator_input.id == link_end_connector_id:
                    return operator_input

    return None


# TODO: replace by link_by_start_id_tuple_dict
def get_link_by_output_connector(
    operator_id: UUID | None, connector_id: UUID, links: list[Link]
) -> Link | None:
    for link in links:
        if (
            link.start.operator == operator_id
            and link.start.connector.id == connector_id
        ):
            return link

    return None


# TODO: replace by link_by_end_id_tuple_dict
def get_link_by_input_connector(
    operator_id: UUID | None, connector_id: UUID, links: list[Link]
) -> Link | None:
    for link in links:
        if link.end.operator == operator_id and link.end.connector.id == connector_id:
            return link

    return None


# TODO: replace by workflow_content_dynamic_input_by_id_dict
def get_input_by_link_start(
    link_start_connector_id: UUID,
    inputs: list[WorkflowContentDynamicInput],
) -> WorkflowContentDynamicInput | None:
    for input_connector in inputs:
        if input_connector.id == link_start_connector_id:
            return input_connector

    return None


# TODO: replace by workflow_content_constant_input_by_id_dict
def get_constant_by_link_start(
    link_start_connector_id: UUID,
    constants: list[WorkflowContentConstantInput],
) -> WorkflowContentConstantInput | None:
    for constant in constants:
        if constant.id == link_start_connector_id:
            return constant

    return None


# TODO: replace by workflow_content_output_by_id_dict
def get_output_by_link_end(
    link_end_connector_id: UUID,
    outputs: list[WorkflowContentOutput],
) -> WorkflowContentOutput | None:
    for output_connector in outputs:
        if output_connector.id == link_end_connector_id:
            return output_connector

    return None


# TODO: replace by workflow_content_dynamic_input_by_operator_id_and_connector_id_dict
def get_input_by_operator_id_and_connector_id(
    operator_id: UUID,
    connector_id: UUID,
    inputs: list[WorkflowContentDynamicInput],
) -> WorkflowContentDynamicInput | None:
    for wf_input in inputs:
        if (
            wf_input.operator_id == operator_id
            and wf_input.connector_id == connector_id
        ):
            return wf_input

    return None


# TODO: replace by workflow_content_output_by_operator_id_and_connector_id_dict
def get_output_by_operator_id_and_connector_id(
    operator_id: UUID,
    connector_id: UUID,
    outputs: list[WorkflowContentOutput],
) -> WorkflowContentOutput | None:
    for output_connector in outputs:
        if (
            output_connector.operator_id == operator_id
            and output_connector.connector_id == connector_id
        ):
            return output_connector

    return None


class WorkflowContent(BaseModel):
    operators: list[Operator] = []
    links: list[Link] = Field([], description="Links may not form loops.")
    inputs: list[WorkflowContentDynamicInput] = Field(
        [],
        description=(
            "Workflow inputs are determined by operator inputs, "
            "which are not connected to links. "
            "If input names are set they must be unique."
        ),
    )
    outputs: list[WorkflowContentOutput] = Field(
        [],
        description=(
            "Workflow outputs are determined by operator outputs, "
            "which are not connected to links. "
            "If output names are set they must be unique."
        ),
    )
    constants: list[WorkflowContentConstantInput] = Field(
        [],
        description=(
            "Constant input values for the workflow are created "
            "by setting a workflow input to a fixed value."
        ),
    )

    @validator("operators", each_item=False)
    def operator_names_unique(cls, operators: list[Operator]) -> list[Operator]:
        """Ensure that operator names are unique.

        This is important to enable the user in case of multiple operators of the same component
        to identify in the IO-dialog the input/output of which component he/she is naming.
        """
        operator_groups: dict[str, list[Operator]] = {}

        for operator in operators:
            operator_name_seed = re.sub(r" \([0-9]+\)$", "", operator.name)
            if operator_name_seed not in operator_groups:
                operator_groups[operator_name_seed] = [operator]
            else:
                operator_groups[operator_name_seed].append(operator)

        for operator_name_seed, operator_group in operator_groups.items():
            if len(operator_group) > 1:
                for index, operator in enumerate(operator_group):
                    if index == 0 and operator.name != NonEmptyValidStr(
                        operator_name_seed
                    ):
                        logger.debug(
                            "Rename operator %s from %s to %s",
                            str(operator.id),
                            operator.name,
                            operator_name_seed,
                        )
                        operator.name = NonEmptyValidStr(operator_name_seed)
                    else:
                        new_name = NonEmptyValidStr(
                            operator_name_seed + " (" + str(index + 1) + ")"
                        )
                        logger.debug(
                            "Rename operator %s from %s to %s",
                            str(operator.id),
                            operator.name,
                            new_name,
                        )
                        operator.name = new_name

        return operators

    @validator("links", each_item=False)
    def clean_up_inner_links(cls, links: list[Link], values: dict) -> list[Link]:
        """Reduce to valid links.

        This validator deals only with links between operator inputs and operator outputs.
        Links between workflow content inputs and operator inputs or between operator outputs and
        workflow content outputs are not touched.

        Delete links for which
        * no operator output with operator id and connector id matching the link start is found or
        * the found operator output does not match to the link start connector or
        * no an operator input with operator id and connector id matching the link end is found or
        * the found operator input does not match to the link end connector
        """
        try:
            operators: list[Operator] = values["operators"]
        except KeyError as error:
            raise ValueError(
                "Cannot reduce to valid links if attribute 'operators' is missing!"
            ) from error

        for link in links:
            if link.start.operator is not None and link.end.operator is not None:
                # links from/to inputs/outputs will be dealt with in the clean_up_io_links validator
                operator_output = get_link_start_connector_from_operator(
                    link.start.operator, link.start.connector.id, operators
                )
                if operator_output is None:
                    logger.warning(
                        "Operator output referenced by link start connector %s "
                        "of link '%s' not found! The link will be removed.",
                        link.start.connector.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
                if not link.start.connector.matches(operator_output):
                    logger.warning(
                        "The link start connector %s and "
                        "the referenced operator output %s "
                        "do not match for link '%s'! The link will be removed.",
                        link.start.connector.json(),
                        operator_output.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue

                operator_input = get_link_end_connector_from_operator(
                    link.end.operator, link.end.connector.id, operators
                )
                if operator_input is None:
                    logger.warning(
                        "Operator input referenced by link end connector %s "
                        "of link '%s' not found! The link will be removed.",
                        link.end.connector.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
                if not link.end.connector.matches(operator_input):
                    logger.warning(
                        "The link end connector %s and the referenced operator input %s "
                        "do not match for link '%s'! The link will be removed.",
                        link.end.connector.json(),
                        operator_input.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
        return links

    @validator("links", each_item=False)
    def links_acyclic_directed_graph(cls, links: list[Link]) -> list[Link]:
        """Ensure the links correspond to an acylic directed graph.

        Transform all links to edges and successively determine the indegrees of all vertices.
        Remove the outgoing edges of vertices with indegree zero and update the other vertice's
        indegrees as long as vertices with indegree zero exist.

        In an acyclic graph finally all vertices will be removed. Thus, if vertices remain these
        are part of a cycle and a validation error is raised.
        """
        indegrees: dict[UUID, int] = {}
        edges: list[tuple[UUID, UUID]] = []

        def add_edge(edge: tuple[UUID, UUID]) -> None:
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
            remove_edges: list[tuple[UUID, UUID]] = []
            for edge in edges:
                if edge[0] == start_vertex:
                    if indegrees[edge[1]] > 0:
                        indegrees[edge[1]] = indegrees[edge[1]] - 1
                    remove_edges.append(edge)
            del indegrees[start_vertex]

            for edge in remove_edges:
                edges.remove(edge)

        def vertices_with_indegree_zero() -> list[UUID]:
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

    @validator("inputs", each_item=False)
    def clean_up_unlinked_workflow_content_inputs(
        cls, inputs: list[WorkflowContentDynamicInput], values: dict
    ) -> list[WorkflowContentDynamicInput]:
        """Cleanup unlinked named dynamic workflow content inputs.

        Delete inputs which have a name but no link start referencing them or a link start
        referencing them with a link end not referencing an operator input.
        """
        try:
            operators: list[Operator] = values["operators"]
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error
        for wf_input in inputs:
            if wf_input.name is not None and wf_input.name != "":
                link = get_link_by_input_connector(
                    wf_input.operator_id, wf_input.connector_id, links
                )
                if link is None:
                    logger.warning(
                        "Link with start connector referencing dynamic workflow content input '%s' "
                        "not found! The input will be removed.",
                        str(wf_input.id),
                    )
                    inputs.remove(wf_input)
                    continue
            operator_input = get_link_end_connector_from_operator(
                wf_input.operator_id, wf_input.connector_id, operators
            )
            if operator_input is None:
                logger.warning(
                    "Link with start connector referencing dynamic workflow input '%s' not found! "
                    "The input will be removed.",
                    str(wf_input.id),
                )
                inputs.remove(wf_input)
                continue
        return inputs

    @validator("inputs", each_item=False)
    def add_workflow_content_inputs_for_unlinked_operator_inputs(
        cls, inputs: list[WorkflowContentDynamicInput], values: dict
    ) -> list[WorkflowContentDynamicInput]:
        """Add dynamic workflow content inputs for unlinked operator inputs.

        Create a new dynamic workflow content input without name for each input of each operator
        that has no link connected to it.
        """
        try:
            operators: list[Operator] = values["operators"]
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot add workflow content inputs for unlinked operator inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        for operator in operators:
            for operator_input in operator.inputs:
                link = get_link_by_input_connector(
                    operator.id, operator_input.id, links
                )
                if link is None:
                    wf_input = get_input_by_operator_id_and_connector_id(
                        operator_id=operator.id,
                        connector_id=operator_input.id,
                        inputs=inputs,
                    )
                    if wf_input is None:
                        logger.warning(
                            "Found no link end connector and no workflow content input for "
                            "operator input %s! Add unnamed worklfow content input.",
                            operator_input.json(),
                        )
                        wf_input = WorkflowContentDynamicInput(
                            data_type=operator_input.data_type,
                            operator_id=operator.id,
                            connector_id=operator_input.id,
                            operator_name=operator.name,
                            connector_name=operator_input.name,
                        )
                        inputs.append(wf_input)

        return inputs

    @validator("outputs", each_item=False)
    def clean_up_unlinked_workflow_content_outputs(
        cls, outputs: list[WorkflowContentOutput], values: dict
    ) -> list[WorkflowContentOutput]:
        """Cleanup unlinked named workflow content outputs.

        Delete outputs which have a name but no link start referencing them or a link start
        referencing them with a link end not referencing an operator input.
        """
        try:
            operators: list[Operator] = values["operators"]
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error
        for wf_output in outputs:
            if wf_output.name is not None and wf_output.name != "":
                link = get_link_by_output_connector(
                    wf_output.operator_id, wf_output.connector_id, links
                )
                if link is None:
                    logger.warning(
                        "Link with end connector referencing workflow output '%s' not found! "
                        "The output will be removed.",
                        str(wf_output.id),
                    )
                    outputs.remove(wf_output)
                    continue
            operator_output = get_link_start_connector_from_operator(
                wf_output.operator_id, wf_output.connector_id, operators
            )
            if operator_output is None:
                logger.warning(
                    "Link with start connector referencing workflow output '%s' found! "
                    "The output will be removed.",
                    str(wf_output.id),
                )
                outputs.remove(wf_output)
                continue
        return outputs

    @validator("outputs", each_item=False)
    def add_workflow_content_outputs_for_unlinked_operator_outputs(
        cls, outputs: list[WorkflowContentOutput], values: dict
    ) -> list[WorkflowContentOutput]:
        """Add workflow content outputs for unlinked operator outputs.

        Create a new workflow content output without name for each output of each operator
        that has no link connected to it.
        """
        try:
            operators: list[Operator] = values["operators"]
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot add workflow content outputs for unlinked operator outputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        for operator in operators:
            for operator_output in operator.outputs:
                link = get_link_by_output_connector(
                    operator.id, operator_output.id, links
                )
                if link is None:
                    wf_output = get_output_by_operator_id_and_connector_id(
                        operator.id, operator_output.id, outputs
                    )
                    if wf_output is None:
                        wf_output = WorkflowContentOutput(
                            data_type=operator_output.data_type,
                            operator_id=operator.id,
                            connector_id=operator_output.id,
                            operator_name=operator.name,
                            connector_name=operator_output.name,
                        )
                        outputs.append(wf_output)
        return outputs

    @validator("inputs", "outputs", each_item=False)
    def connector_names_empty_or_unique(
        cls, workflow_ios: list[WorkflowContentIO]
    ) -> list[WorkflowContentIO]:
        """Ensure the names of workflow inputs and outputs are unique, respectively.

        Test separately for those workflow content inputs and those workflow content outputs, which
        have a name (i.e. it is not None and not an empty string), that their names are unique.
        Otherwise raise a value error.
        """
        workflow_ios_with_nonempty_name = [
            workflow_io
            for workflow_io in workflow_ios
            if not (workflow_io.name is None or workflow_io.name == "")
        ]

        names_unique(cls, workflow_ios_with_nonempty_name)

        return workflow_ios

    @root_validator()
    def clean_up_outer_links(cls, values: dict) -> dict:
        """Clean up outer links.

        For links from a dynamic/constant workflow content input to an operator input and for links
        from an operator output to a workflow content output it is checked if the referenced
        entities exist and match to the link start and end connector.
        If they do not exist or do not match the link is removed and an according message is logged.

        New links for named inputs are added by the frontend before sending the PUT-request.
        """
        try:
            operators: list[Operator] = values["operators"]
            links: list[Link] = values["links"]
            constants: list[WorkflowContentConstantInput] = values["constants"]
            inputs: list[WorkflowContentDynamicInput] = values["inputs"]
            outputs: list[WorkflowContentOutput] = values["outputs"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up io links if any of the attributes "
                "'operators', 'links', 'inputs' and 'outputs' is missing!"
            ) from error

        for link in links:
            if link.start.operator is None:
                # thus the link is from a workflow content input to an operator output
                workflow_content_dynamic_input = get_input_by_link_start(
                    link.start.connector.id, inputs
                )
                if workflow_content_dynamic_input is not None:
                    if workflow_content_dynamic_input.name == "":
                        logger.warning(
                            "Dynamic workflow input %s referenced by link start connector %s "
                            "of link '%s' has no name! The link will be removed.",
                            workflow_content_dynamic_input.json(),
                            link.start.connector.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue

                    operator_input = get_link_end_connector_from_operator(
                        link.end.operator, link.end.connector.id, operators
                    )
                    if operator_input is None:
                        logger.warning(
                            "Operator input referenced by link end connector %s "
                            "of link '%s' not found! The link will be removed.",
                            link.end.connector.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue

                    if not link.start.connector.matches(workflow_content_dynamic_input):
                        logger.warning(
                            "The link start connector %s and the referenced dynamic workflow "
                            "input %s do not match for link '%s'! The link will be removed.",
                            link.start.connector.json(),
                            workflow_content_dynamic_input.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue
                    if not link.end.connector.matches(operator_input):
                        logger.warning(
                            "The link end connector %s and the referenced operator input %s "
                            "do not match for link '%s'! The link will be removed.",
                            link.end.connector.json(),
                            operator_input.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue
                else:
                    workflow_content_constant_input = get_constant_by_link_start(
                        link.start.connector.id, constants
                    )
                    if workflow_content_constant_input is None:
                        logger.warning(
                            "Neither dynamic workflow input nor constant workflow input "
                            "referenced by link start connector %s of link '%s' found! "
                            "The link will be removed.",
                            link.start.connector.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue

                    operator_input = get_link_end_connector_from_operator(
                        link.end.operator, link.end.connector.id, operators
                    )
                    if operator_input is None:
                        logger.warning(
                            "Operator input referenced by link end connector %s "
                            "of link '%s' not found! The link will be removed.",
                            link.end.connector.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue

                    if not link.start.connector.matches(
                        workflow_content_constant_input
                    ):
                        logger.warning(
                            "The link start connector %s and the referenced constant workflow "
                            "input %s do not match for link '%s'! The link will be removed.",
                            link.start.connector.json(),
                            workflow_content_constant_input,
                            str(link.id),
                        )
                        links.remove(link)
                        continue
                    if not link.end.connector.matches(operator_input):
                        logger.warning(
                            "The link end connector %s and the referenced operator input %s "
                            "do not match for link '%s'! The link will be removed.",
                            link.end.connector.json(),
                            operator_input.json(),
                            str(link.id),
                        )
                        links.remove(link)
                        continue
            elif link.end.operator is None:
                # thus the link is from a workflow content input to an operator output
                workflow_content_output = get_output_by_link_end(
                    link.end.connector.id, outputs
                )
                if workflow_content_output is None:
                    logger.warning(
                        "Workflow output referenced by link end connector %s "
                        "of link '%s' not found! The link will be removed.",
                        link.end.connector.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
                if workflow_content_output.name == "":
                    logger.warning(
                        "Workflow output %s referenced by link end connector %s "
                        "of link '%s' has no name! The link will be removed.",
                        workflow_content_output.json(),
                        link.end.connector.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue

                operator_output = get_link_start_connector_from_operator(
                    link.start.operator, link.start.connector.id, operators
                )
                if operator_output is None:
                    logger.warning(
                        "Operator output referenced by link start connector %s "
                        "of link '%s' not found! The link will be removed.",
                        link.start.connector.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue

                if not link.start.connector.matches(operator_output):
                    logger.warning(
                        "The link start connector %s and "
                        "the referenced operator output %s "
                        "do not match for link '%s'! The link will be removed.",
                        link.start.connector.json(),
                        operator_output.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
                if not link.end.connector.matches(workflow_content_output):
                    logger.warning(
                        "The link end connector %s and "
                        "the referenced workflow output %s "
                        "do not match for link '%s'! The link will be removed.",
                        link.end.connector.json(),
                        workflow_content_output.json(),
                        str(link.id),
                    )
                    links.remove(link)
                    continue
        return values

        return values

    def to_workflow_node(
        self,
        transformation_id: UUID,
        transformation_name: str,
        transformation_tag: str,
        operator_id: UUID | None,
        operator_name: str | None,
        sub_nodes: list[WorkflowNode | ComponentNode],
    ) -> WorkflowNode:
        inputs = []
        for input_connector in self.inputs:
            inputs.append(input_connector.to_workflow_input())
        for constant in self.constants:
            inputs.append(constant.to_workflow_input())

        outputs = []
        for output_connector in self.outputs:
            outputs.append(output_connector.to_workflow_output())

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
            name=operator_name,
            tr_id=str(transformation_id),
            tr_name=transformation_name,
            tr_tag=transformation_tag,
        )

    class Config:
        validate_assignment = True
