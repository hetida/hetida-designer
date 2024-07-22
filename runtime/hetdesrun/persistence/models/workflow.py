import logging
import re
from contextlib import suppress
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


def wf_input_unnecessary(
    wf_input: WorkflowContentDynamicInput,
    operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput],
    link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link],
) -> bool:
    """Check if a dynamic workflow content input is unnecessary based on their operator input.

    Unnecessary dynamic workflow content inputs reference an operator input, that
        * does not exist,
        * does not match,
        * is not exposed or
        * has a link with a start not matching the workflow content input.
    """
    try:
        operator_input = operator_input_by_id_tuple_dict[
            (wf_input.operator_id, wf_input.connector_id)
        ]
    except KeyError:
        logger.warning(
            "Operator input referenced by dynamic workflow input '%s' not found! "
            "The input will be removed.",
            str(wf_input.id),
        )
        return True
    if not wf_input.matches_operator_io(operator_input):
        logger.warning(
            "Operator input referenced by dynamic workflow input '%s' does not match! "
            "The input will be removed.",
            str(wf_input.id),
        )
        return True
    if operator_input.exposed is False:
        logger.warning(
            "Operator input referenced by dynamic workflow input '%s' is not exposed! "
            "The input will be removed.",
            str(wf_input.id),
        )
        return True
    try:
        link_to_operator_input = link_by_end_id_tuple_dict[
            (
                wf_input.operator_id,
                wf_input.connector_id,
            )
        ]
    except KeyError:
        pass
    else:
        if wf_input.id != link_to_operator_input.start.connector.id:
            logger.warning(
                "Operator input referenced by dynamic workflow input '%s' has a link "
                "with a start id not matching the input id! The input will be removed.",
                str(wf_input.id),
            )
            return True
    return False


def named_wf_input_unnecessary(
    wf_input: WorkflowContentDynamicInput,
    links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]],
) -> bool:
    """Check if a named dynamic workflow content input is unnecessary based on their link.

    Unnecessary named dynamic workflow content inputs have
        * no link,
        * a link with a start not matching them or
        * a link with an end not referencing the operator input referenced by the input itself.
    """
    try:
        links_starting_at_workflow_input = links_by_start_id_tuple_dict[(None, wf_input.id)]
    except KeyError:
        logger.warning(
            "Link with start connector referencing dynamic workflow content input '%s' "
            "not found! The input will be removed.",
            str(wf_input.id),
        )
        return True
    if len(links_starting_at_workflow_input) > 1:
        msg = (
            "There is more than one link starting from "
            f"dynamic workflow content input '{str(wf_input.id)}'."
        )
        logger.error(msg)
        raise ValueError(msg)
    link_at_workflow_input = links_starting_at_workflow_input[0]
    if not wf_input.matches_io(link_at_workflow_input.start.connector):
        # TODO: change to matches_connector once the frontend has been updated
        logger.warning(
            "Link start connector referencing dynamic workflow content input '%s' does "
            "not match! The input will be removed.",
            str(wf_input.id),
        )
        return True
    if wf_input.position != link_at_workflow_input.start.connector.position:
        # TODO: remove this check once the above one has changed to machtes_connector
        logger.warning(
            "The position of the link start connector referencing dynamic workflow "
            "content input '%s' does not match the position of the dynamic workflow "
            "content input! The link start connector position will be adjusted.",
            str(wf_input.id),
        )
        link_at_workflow_input.start.connector.position = wf_input.position
    # Operator input matches link end connector already checked
    # in validator link_connectors_match_operator_ios.
    if (
        link_at_workflow_input.end.operator != wf_input.operator_id
        or link_at_workflow_input.end.connector.id != wf_input.connector_id
    ):
        logger.warning(
            "Link with start connector referencing dynamic workflow content input '%s' "
            "has end connector referencing different operator input than the worfklow "
            "input! The input will be removed.",
            str(wf_input.id),
        )
        return True
    return False


def wf_output_unnecessary(
    wf_output: WorkflowContentOutput,
    operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput],
    links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]],
) -> bool:
    """Check if a workflow content output is unnecessary based on their operator output.

    Unnecessary workflow content outputs referenced an operator output, that
        * does not exist,
        * does not match or
        * has a link with an end not matching the workflow content output.
    """
    try:
        operator_output = operator_output_by_id_tuple_dict[
            (wf_output.operator_id, wf_output.connector_id)
        ]
    except KeyError:
        logger.warning(
            "Operator output referenced by workflow output '%s' not found! "
            "The output will be removed.",
            str(wf_output.id),
        )
        return True
    if not wf_output.matches_operator_io(operator_output):
        logger.warning(
            "Operator output referenced by workflow output '%s' does not match! "
            "The output will be removed.",
            str(wf_output.id),
        )
        return True
    try:
        links_starting_at_operator_output = links_by_start_id_tuple_dict[
            (
                wf_output.operator_id,
                wf_output.connector_id,
            )
        ]
    except KeyError:
        pass
    else:
        if any(wf_output.id != link.end.connector.id for link in links_starting_at_operator_output):
            logger.warning(
                "Operator output referenced by workflow output '%s' has a link with an"
                "end id not matching the output id! The output will be removed.",
                str(wf_output.id),
            )
            return True
    return False


def named_wf_output_unnecessary(
    wf_output: WorkflowContentOutput,
    link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link],
) -> bool:
    """Check if a named workflow content output is unnecessary.

    Unnecessary named workflow content outputs have
        * no link,
        * a link end not matching them or
        * a link with a start not referencing the operator input referenced by the output itself.
    """
    try:
        link = link_by_end_id_tuple_dict[(None, wf_output.id)]
    except KeyError:
        logger.warning(
            "Link with end connector referencing workflow output '%s' not found! "
            "The output will be removed.",
            str(wf_output.id),
        )
        return True
    if not wf_output.matches_io(link.end.connector):
        # TODO: change to matches_connector once the frontend has been updated
        logger.warning(
            "Link end connector referencing workflow content output '%s' does "
            "not match! The output will be removed.",
            str(wf_output.id),
        )
        return True
    if wf_output.position != link.end.connector.position:
        # TODO: remove this check once the above one has changed to machtes_connector
        logger.warning(
            "The position of the link end connector referencing workflow content "
            "output '%s' does not match the workflow content output position! "
            "The link end connector position will be adjusted.",
            str(wf_output.id),
        )
        link.end.connector.position = wf_output.position
    # Operator output matches link start connector already checked
    # in validator link_connectors_match_operator_ios.
    if (
        link.start.operator != wf_output.operator_id
        or link.start.connector.id != wf_output.connector_id
    ):
        logger.warning(
            "Link with end connector referencing workflow content output '%s' "
            "has start connector referencing different operator output than the "
            "worfklow output! The output will be removed.",
            str(wf_output.id),
        )
        return True
    return False


def link_invalid_due_to_operator_output(
    link: Link,
    operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput],
) -> bool:
    """Check if link is invalid tue to the referenced operator output.

    Links are invalid if
        * no operator output with operator id and connector id matching the link start is found or
        * the found operator output does not match to the link start connector.

    """
    if link.start.operator is None:
        raise ValueError(
            "Function link_invalid_due_to_operator_output intended exclusively for links which "
            f"start at an operator output, i.e. link '{link.id}' start operator may not be None."
        )
    try:
        operator_output = operator_output_by_id_tuple_dict[
            (link.start.operator, link.start.connector.id)
        ]
    except KeyError:
        logger.warning(
            "Operator output referenced by link '%s' start connector '%s' "
            "not found! The link will be removed.",
            str(link.id),
            str(link.start.connector.id),
        )
        return True
    if not link.start.connector.matches_connector(operator_output):
        logger.warning(
            "The link '%s' start connector '%s' and "
            "the referenced operator output "
            "do not match! The link will be removed.",
            str(link.id),
            str(link.start.connector.id),
        )
        return True
    return False


def link_invalid_due_to_operator_input(
    link: Link, operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput]
) -> bool:
    """Check if link is invalid tue to the referenced operator input.

    Links are invalid if
        * no an operator input with operator id and connector id matching the link end is found,
        * the found operator input does not match to the link end connector or
        * the found operator input is not exposed.
    """
    if link.end.operator is None:
        raise ValueError(
            "Function link_invalid_due_to_operator_input intended exclusively for links which "
            f"end at an operator input, i.e. link '{link.id}' end operator may not be None."
        )
    try:
        operator_input = operator_input_by_id_tuple_dict[(link.end.operator, link.end.connector.id)]
    except KeyError:
        logger.warning(
            "Operator input referenced by link '%s' end connector '%s' "
            "not found! The link will be removed.",
            str(link.id),
            str(link.end.connector.id),
        )
        return True
    if not link.end.connector.matches_connector(operator_input):
        logger.warning(
            "The link '%s' end connector '%s' and the referenced operator input "
            "do not match! The link will be removed.",
            str(link.id),
            str(link.end.connector.id),
        )
        return True
    if operator_input.exposed is False:
        logger.warning(
            "The link '%s' end connector '%s' references a not exposed operator input! "
            "The link will be removed.",
            str(link.id),
            str(link.end.connector.id),
        )
        return True
    return False


def outer_link_invalid_due_to_workflow_input(
    link: Link,
    workflow_content_input_by_id_dict: dict[UUID, WorkflowContentIO],
) -> bool:
    """Check if link is invalid tue to the referenced workflow input.

    Links from a dynamic/constant workflow content input to an operator input are invalid if
        * the referenced dynamic/constant workflow content input does not exist or
        * the referenced dynamic/constant workflow content input has no name.
    """
    try:
        workflow_content_input = workflow_content_input_by_id_dict[link.start.connector.id]
    except KeyError:
        logger.warning(
            "Workflow input referenced by link '%s' start connector '%s' "
            "not found! The link will be removed.",
            str(link.id),
            str(link.start.connector.id),
        )
        return True
    else:
        # the workflow_content_input referenced by the link is found
        if isinstance(workflow_content_input, WorkflowContentDynamicInput) and (
            workflow_content_input.name is None or workflow_content_input.name == ""
        ):
            logger.warning(
                "Workflow input '%s' referenced by link '%s' start connector '%s' "
                "has no name! The link will be removed.",
                str(workflow_content_input.id),
                str(link.id),
                str(link.start.connector.id),
            )
            return True
    return False


def outer_link_invalid_due_to_workflow_output(
    link: Link,
    workflow_content_output_by_id_dict: dict[UUID, WorkflowContentOutput],
) -> bool:
    """Check if link is invalid tue to the referenced workflow output.

    Links from an operator input to a workflow content output are invalid if
        * the referenced workflow content output does not exist or
        * the referenced workflow content output has no name.
    """
    try:
        workflow_content_output = workflow_content_output_by_id_dict[link.end.connector.id]
    except KeyError:
        logger.warning(
            "Workflow output referenced by link '%s' end connector '%s' "
            "not found! The link will be removed.",
            str(link.id),
            str(link.end.connector.id),
        )
        return True
    if workflow_content_output.name is None or workflow_content_output.name == "":
        logger.warning(
            "Workflow output '%s' referenced by link  '%s' end connector '%s' "
            "has no name! The link will be removed.",
            str(workflow_content_output.id),
            str(link.id),
            str(link.end.connector.id),
        )
        return True
    return False


class WorkflowContent(BaseModel):
    operators: list[Operator] = []
    operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput] = Field(
        {}, description="This field is only used for validation and removed afterwards."
    )
    operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput] = Field(
        {}, description="This field is only used for validation and removed afterwards."
    )
    links: list[Link] = Field([], description="Links may not form loops.")
    links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]] = Field(
        {},
        description=(
            "This field is only used for validation and removed afterwards. "
            "At dynamic workflow content inputs at most one link starts, "
            "but at operator outputs more than one link may start."
        ),
    )
    link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link] = Field(
        {},
        description=(
            "This field is only used for validation and removed afterwards. Both at workflow "
            "content outputs and operator inputs at most one link ends."
        ),
    )
    constants: list[WorkflowContentConstantInput] = Field(
        [],
        description=(
            "Constant input values for the workflow are created "
            "by setting a workflow input to a fixed value."
        ),
    )
    inputs: list[WorkflowContentDynamicInput] = Field(
        [],
        description=(
            "Workflow inputs are determined by operator inputs, "
            "which are not connected to other operators via links. "
            "If input names are set they must be unique."
        ),
    )
    outputs: list[WorkflowContentOutput] = Field(
        [],
        description=(
            "Workflow outputs are determined by operator outputs, "
            "which are not connected to other operators via links. "
            "If output names are set they must be unique."
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
                    if index == 0:
                        if operator.name != NonEmptyValidStr(operator_name_seed):
                            logger.debug(
                                "Rename operator '%s' from '%s' to '%s'",
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
                            "Rename operator '%s' from '%s' to '%s'",
                            str(operator.id),
                            operator.name,
                            new_name,
                        )
                        operator.name = new_name
            else:
                operator_group[0].name = NonEmptyValidStr(operator_name_seed)

        return operators

    @validator("operator_output_by_id_tuple_dict", always=True)
    def initialize_operator_output_by_id_tuple_dict(
        cls,
        operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput],
        values: dict,
    ) -> dict[tuple[UUID, UUID], OperatorOutput]:
        """Initialize operator output by operator and connector id tuple dictionary."""
        try:
            operators: list[Operator] = values["operators"]
        except KeyError as error:
            raise ValueError(
                "Cannot initialize operator output by id tuple dict "
                "if attribute 'operators' is missing!"
            ) from error
        operator_output_by_id_tuple_dict = {
            (operator.id, operator_output.id): operator_output
            for operator in operators
            for operator_output in operator.outputs
        }
        return operator_output_by_id_tuple_dict

    @validator("operator_input_by_id_tuple_dict", always=True)
    def initialize_operator_input_by_id_tuple_dict(
        cls,
        operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput],
        values: dict,
    ) -> dict[tuple[UUID, UUID], OperatorInput]:
        """Initialize operator input by operator and connector id tuple dictionary."""
        try:
            operators: list[Operator] = values["operators"]
        except KeyError as error:
            raise ValueError(
                "Cannot initialize operator output by id tuple dict "
                "if attribute 'operators' is missing!"
            ) from error
        operator_input_by_id_tuple_dict = {
            (operator.id, operator_input.id): operator_input
            for operator in operators
            for operator_input in operator.inputs
        }
        return operator_input_by_id_tuple_dict

    @validator("links", each_item=False)
    def link_connectors_match_operator_ios(cls, links: list[Link], values: dict) -> list[Link]:
        """Delete links with missing or not matching operator inputs or outputs.

        Delete links for which
        * no operator output with operator id and connector id matching the link start is found,
        * the found operator output does not match to the link start connector,
        * no an operator input with operator id and connector id matching the link end is found,
        * the found operator input does not match to the link end connector or
        * the found operator input is not exposed.
        """
        try:
            operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput] = values[
                "operator_input_by_id_tuple_dict"
            ]
            operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput] = values[
                "operator_output_by_id_tuple_dict"
            ]
        except KeyError as error:
            raise ValueError(
                "Cannot reduce to valid links if attribute 'operators' is missing!"
            ) from error

        remove_links = []
        for link in links:
            # Since link start and end operators may not be the same, they cannot both be None
            if link.start.operator is not None and link_invalid_due_to_operator_output(
                link, operator_output_by_id_tuple_dict
            ):
                remove_links.append(link)
                continue
            if link.end.operator is not None and link_invalid_due_to_operator_input(
                link, operator_input_by_id_tuple_dict
            ):
                remove_links.append(link)

        for link in remove_links:
            links.remove(link)

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

    @validator("links_by_start_id_tuple_dict", always=True)
    def initialize_links_by_start_id_tuple_dict(
        cls,
        links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]],
        values: dict,
    ) -> dict[tuple[UUID | None, UUID], list[Link]]:
        """Initialize link by start operator and connector id tuple dictionary."""
        try:
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        links_by_start_id_tuple_dict = {}
        for link in links:
            if (
                link.start.operator,
                link.start.connector.id,
            ) not in links_by_start_id_tuple_dict:
                links_by_start_id_tuple_dict[(link.start.operator, link.start.connector.id)] = []
            links_by_start_id_tuple_dict[(link.start.operator, link.start.connector.id)].append(
                link
            )
        return links_by_start_id_tuple_dict

    @validator("link_by_end_id_tuple_dict", always=True)
    def initialize_link_by_end_id_tuple_dict(
        cls,
        link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link],
        values: dict,
    ) -> dict[tuple[UUID | None, UUID], Link]:
        """Initialize link by end operator and connector id tuple dictionary."""
        try:
            links: list[Link] = values["links"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error
        link_by_end_id_tuple_dict = {
            (link.end.operator, link.end.connector.id): link for link in links
        }
        return link_by_end_id_tuple_dict

    @validator("inputs", each_item=False)
    def clean_up_workflow_content_inputs(
        cls, inputs: list[WorkflowContentDynamicInput], values: dict
    ) -> list[WorkflowContentDynamicInput]:
        """Cleanup unlinked (or wrongly linked named) dynamic workflow content inputs.

        Delete unnecessary dynamic workflow content inputs based on the referenced operator input.
        Delete unnecessary named dynamic workflow content inputs based on the link starting at them.
        """
        try:
            operator_input_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorInput] = values[
                "operator_input_by_id_tuple_dict"
            ]
            links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]] = values[
                "links_by_start_id_tuple_dict"
            ]
            link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link] = values[
                "link_by_end_id_tuple_dict"
            ]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        remove_wf_inputs = []
        for wf_input in inputs:
            if (
                wf_input_unnecessary(
                    wf_input, operator_input_by_id_tuple_dict, link_by_end_id_tuple_dict
                )
                is True
            ):
                remove_wf_inputs.append(wf_input)
                continue
            if (
                wf_input.name is not None
                and wf_input.name != ""
                and named_wf_input_unnecessary(wf_input, links_by_start_id_tuple_dict) is True
            ):
                remove_wf_inputs.append(wf_input)

        for wf_input in remove_wf_inputs:
            inputs.remove(wf_input)

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
            constants: list[WorkflowContentConstantInput] = values["constants"]
            link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link] = values[
                "link_by_end_id_tuple_dict"
            ]
        except KeyError as error:
            raise ValueError(
                "Cannot add workflow content inputs for unlinked operator inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        wf_input_by_operator_and_connector_id_dict: dict[tuple[UUID, UUID], WorkflowContentIO] = {
            (wf_input.operator_id, wf_input.connector_id): wf_input for wf_input in inputs
        }
        wf_input_by_operator_and_connector_id_dict.update(
            {(wf_input.operator_id, wf_input.connector_id): wf_input for wf_input in constants}
        )

        for operator in operators:
            for operator_input in operator.inputs:
                if operator_input.exposed is False:
                    continue
                try:
                    wf_input_by_operator_and_connector_id_dict[
                        (
                            operator.id,
                            operator_input.id,
                        )
                    ]
                except KeyError:
                    try:
                        link = link_by_end_id_tuple_dict[(operator.id, operator_input.id)]
                    except KeyError:
                        logger.warning(
                            "Found no workflow content input and no link end connector for "
                            "operator '%s' input '%s'! Add unnamed workflow content input.",
                            str(operator.id),
                            str(operator_input.id),
                        )
                        wf_input = WorkflowContentDynamicInput(
                            data_type=operator_input.data_type,
                            operator_id=operator.id,
                            connector_id=operator_input.id,
                            operator_name=operator.name,
                            connector_name=operator_input.name,
                        )
                        inputs.append(wf_input)
                        continue
                    # If operator input is linked to operator output nothing needs to be done
                    if link.start.operator is None:
                        logger.warning(
                            "Found no workflow content input but a link with start connector "
                            "referencing a workflow content input for operator '%s' input '%s'! "
                            "Add unnamed workflow content input.",
                            str(operator.id),
                            str(operator_input.id),
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
    def clean_up_workflow_content_outputs(
        cls, outputs: list[WorkflowContentOutput], values: dict
    ) -> list[WorkflowContentOutput]:
        """Cleanup unlinked (or wrongly linked named) workflow content outputs.

        Delete unnecessary workflow content outputs based on the referenced operator output.
        Delete unnecessary named workflow content outputs based on the link ending at them.
        """
        try:
            links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]] = values[
                "links_by_start_id_tuple_dict"
            ]
            link_by_end_id_tuple_dict: dict[tuple[UUID | None, UUID], Link] = values[
                "link_by_end_id_tuple_dict"
            ]
            operator_output_by_id_tuple_dict: dict[tuple[UUID, UUID], OperatorOutput] = values[
                "operator_output_by_id_tuple_dict"
            ]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up unlinked inputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        remove_wf_outputs = []
        for wf_output in outputs:
            if (
                wf_output_unnecessary(
                    wf_output,
                    operator_output_by_id_tuple_dict,
                    links_by_start_id_tuple_dict,
                )
                is True
            ):
                remove_wf_outputs.append(wf_output)
                continue
            if (
                wf_output.name is not None
                and wf_output.name != ""
                and named_wf_output_unnecessary(wf_output, link_by_end_id_tuple_dict) is True
            ):
                remove_wf_outputs.append(wf_output)

        for wf_output in remove_wf_outputs:
            outputs.remove(wf_output)

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
            links_by_start_id_tuple_dict: dict[tuple[UUID | None, UUID], list[Link]] = values[
                "links_by_start_id_tuple_dict"
            ]
        except KeyError as error:
            raise ValueError(
                "Cannot add workflow content outputs for unlinked operator outputs "
                "if any of the attributes 'operators', 'links' is missing!"
            ) from error

        wf_output_by_operator_and_connector_id_dict = {
            (wf_output.operator_id, wf_output.connector_id): wf_output for wf_output in outputs
        }

        for operator in operators:
            for operator_output in operator.outputs:
                try:
                    wf_output_by_operator_and_connector_id_dict[(operator.id, operator_output.id)]
                except KeyError:
                    try:
                        links_starting_at_operator_output = links_by_start_id_tuple_dict[
                            (operator.id, operator_output.id)
                        ]
                    except KeyError:
                        logger.warning(
                            "Found no workflow content output and no link start connector for "
                            "operator '%s' output '%s'! Add unnamed workflow content output.",
                            str(operator.id),
                            str(operator_output.id),
                        )
                        wf_output = WorkflowContentOutput(
                            data_type=operator_output.data_type,
                            operator_id=operator.id,
                            connector_id=operator_output.id,
                            operator_name=operator.name,
                            connector_name=operator_output.name,
                        )
                        outputs.append(wf_output)
                        continue
                    # If operator output is linked to operator input nothing needs to be done
                    if None in (link.end.operator for link in links_starting_at_operator_output):
                        logger.warning(
                            "Found no workflow content output but a link with start connector "
                            "referencing a workflow content output for operator '%s' output '%s'! "
                            "Add unnamed workflow content output.",
                            str(operator.id),
                            str(operator_output.id),
                        )
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
    def workflow_content_io_names_empty_or_unique(
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

        Delete links which are invalid due to the referenced workflow content input.
        Delete links which are invalid due to the referenced workflow content output.

        New links for named inputs are added by the frontend before sending the PUT-request.
        """
        try:
            links: list[Link] = values["links"]
            constants: list[WorkflowContentConstantInput] = values["constants"]
            inputs: list[WorkflowContentDynamicInput] = values["inputs"]
            outputs: list[WorkflowContentOutput] = values["outputs"]
        except KeyError as error:
            raise ValueError(
                "Cannot clean up io links if any of the attributes "
                "'operators', 'links', 'inputs' and 'outputs' is missing!"
            ) from error

        workflow_content_input_by_id_dict: dict[UUID, WorkflowContentIO] = {
            wf_input.id: wf_input for wf_input in inputs
        }
        workflow_content_input_by_id_dict.update({wf_input.id: wf_input for wf_input in constants})
        workflow_content_output_by_id_dict: dict[UUID, WorkflowContentOutput] = {
            wf_output.id: wf_output for wf_output in outputs
        }

        remove_links = []
        for link in links:
            if (
                link.start.operator is None  # the link is from a worklfo input to an operator input
                and outer_link_invalid_due_to_workflow_input(
                    link, workflow_content_input_by_id_dict
                )
                is True
            ):
                remove_links.append(link)
                continue
            if (
                link.end.operator is None
                # the link is from an operator output to a workflow output
                and outer_link_invalid_due_to_workflow_output(
                    link, workflow_content_output_by_id_dict
                )
                is True
            ):
                remove_links.append(link)

        for link in remove_links:
            links.remove(link)

        return values

    @root_validator()
    def clean_up_dicts(cls, values: dict) -> dict:
        """Delete validation helper dictionaries."""
        with suppress(KeyError):
            values["operator_output_by_id_tuple_dict"] = {}
            values["operator_input_by_id_tuple_dict"] = {}
            values["links_by_start_id_tuple_dict"] = {}
            values["link_by_end_id_tuple_dict"] = {}

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
        for wf_input in self.inputs:
            inputs.append(wf_input.to_workflow_input())
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
        frozen = True
        fields = {
            "operator_output_by_id_tuple_dict": {"exclude": True},
            "operator_input_by_id_tuple_dict": {"exclude": True},
            "links_by_start_id_tuple_dict": {"exclude": True},
            "link_by_end_id_tuple_dict": {"exclude": True},
        }
