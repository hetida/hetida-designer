import re
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import root_validator, validator

from hetdesrun.backend.models.info import BasicInformation
from hetdesrun.backend.models.io import ConnectorFrontendDto, WorkflowIoFrontendDto
from hetdesrun.backend.models.link import WorkflowLinkFrontendDto
from hetdesrun.backend.models.operator import WorkflowOperatorFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.datatypes import DataType
from hetdesrun.models.util import names_unique
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.link import Link
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type


def get_operator_and_connector_name(
    operator_id: UUID, connector_id: UUID, operators: list[WorkflowOperatorFrontendDto]
) -> tuple[str, str]:
    operator_name: str = "operator name"
    connector_name: str = "connector_name"
    for operator in operators:
        if operator.id == operator_id:
            operator_name = operator.name
            for connector in operator.inputs:
                if connector.id == connector_id:
                    assert isinstance(connector.name, str)  # hint for mypy # noqa: S101
                    connector_name = connector.name
            for connector in operator.outputs:
                if connector.id == connector_id:
                    assert isinstance(connector.name, str)  # hint for mypy # noqa: S101
                    connector_name = connector.name
    return operator_name, connector_name


def is_link_start(
    operator_id: UUID,
    connector_id: UUID,
    links: list[WorkflowLinkFrontendDto],
    workflow_id: UUID,
) -> bool:
    for link in links:
        if (
            link.from_operator == operator_id
            and link.from_connector == connector_id
            and link.to_operator != workflow_id
        ):
            return True

    return False


def is_link_end(
    operator_id: UUID,
    connector_id: UUID,
    links: list[WorkflowLinkFrontendDto],
    workflow_id: UUID,
) -> bool:
    for link in links:
        if (
            link.to_operator == operator_id
            and link.to_connector == connector_id
            and link.from_operator != workflow_id
        ):
            return True

    return False


def is_connected_to_input(
    operator_id: UUID, connector_id: UUID, inputs: list[WorkflowIoFrontendDto]
) -> bool:
    return any(inp.operator == operator_id and inp.connector == connector_id for inp in inputs)


def is_connected_to_output(
    operator_id: UUID, connector_id: UUID, outputs: list[WorkflowIoFrontendDto]
) -> bool:
    for output in outputs:
        if output.operator == operator_id and output.connector == connector_id:
            return True

    return False


def get_or_create_input(
    operator_id: UUID,
    connector_id: UUID,
    type: DataType,  # noqa: A002
    inputs: list[WorkflowIoFrontendDto],
) -> WorkflowIoFrontendDto:
    matching_inputs: list[WorkflowIoFrontendDto] = []

    for inp in inputs:
        if inp.operator == operator_id and inp.connector == connector_id:
            inp.type = type
            matching_inputs.append(inp)

    if len(matching_inputs) > 0:
        return matching_inputs[0]

    return WorkflowIoFrontendDto(operator=operator_id, connector=connector_id, type=type)


def get_or_create_output(
    operator_id: UUID,
    connector_id: UUID,
    type: DataType,  # noqa: A002
    outputs: list[WorkflowIoFrontendDto],
) -> WorkflowIoFrontendDto:
    matching_outputs: list[WorkflowIoFrontendDto] = []

    for output in outputs:
        if output.operator == operator_id and output.connector == connector_id:
            output.type = type
            matching_outputs.append(output)

    if len(matching_outputs) > 0:
        return matching_outputs[0]

    return WorkflowIoFrontendDto(operator=operator_id, connector=connector_id, type=type)


def get_link_start_type_from_operator(
    link: WorkflowLinkFrontendDto,
    operators: list[WorkflowOperatorFrontendDto],
) -> DataType | None:
    data_type: DataType | None = None

    for operator in operators:
        if operator.id == link.from_operator:
            for connector in operator.outputs:
                if connector.id == link.from_connector:
                    data_type = connector.type

    return data_type


def get_link_start_type_from_input(
    link: WorkflowLinkFrontendDto,
    inputs: list[WorkflowIoFrontendDto],
) -> DataType | None:
    data_type: DataType | None = None

    for inp in inputs:
        if inp.id == link.from_connector:
            data_type = inp.type

    return data_type


def get_link_end_type_from_operator(
    link: WorkflowLinkFrontendDto,
    operators: list[WorkflowOperatorFrontendDto],
) -> DataType | None:
    data_type: DataType | None = None

    for operator in operators:
        if operator.id == link.to_operator:
            for connector in operator.inputs:
                if connector.id == link.to_connector:
                    data_type = connector.type

    return data_type


def get_link_end_type_from_output(
    link: WorkflowLinkFrontendDto,
    outputs: list[WorkflowIoFrontendDto],
) -> DataType | None:
    data_type: DataType | None = None

    for output in outputs:
        if output.id == link.to_connector:
            data_type = output.type

    return data_type


def get_input_name_from_link(
    link: WorkflowLinkFrontendDto,
    inputs: list[WorkflowIoFrontendDto],
) -> str | None:
    name: str | None = None

    for inp in inputs:
        if inp.id == link.from_connector:
            name = inp.name

    return name


def get_output_name_from_link(
    link: WorkflowLinkFrontendDto,
    outputs: list[WorkflowIoFrontendDto],
) -> str | None:
    name: str | None = None

    for output in outputs:
        if output.id == link.to_connector:
            name = output.name

    return name


class WorkflowRevisionFrontendDto(BasicInformation):
    type: Literal[Type.WORKFLOW] = Type.WORKFLOW  # noqa: A003
    operators: list[WorkflowOperatorFrontendDto] = []
    links: list[WorkflowLinkFrontendDto] = []
    inputs: list[WorkflowIoFrontendDto] = []
    outputs: list[WorkflowIoFrontendDto] = []
    wirings: list[WiringFrontendDto] = []

    @validator("operators", each_item=False)
    def operator_names_unique(
        cls, operators: list[WorkflowOperatorFrontendDto]
    ) -> list[WorkflowOperatorFrontendDto]:
        operator_groups: dict[str, list[WorkflowOperatorFrontendDto]] = {}

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
                        operator.name = operator_name_seed
                    else:
                        operator.name = operator_name_seed + " (" + str(index + 1) + ")"

        return operators

    @validator("links", each_item=False)
    def reduce_to_valid_links(
        cls, links: list[WorkflowLinkFrontendDto], values: dict
    ) -> list[WorkflowLinkFrontendDto]:
        try:
            operators = values["operators"]
            workflow_id = values["id"]
        except KeyError as e:
            raise ValueError(
                "Cannot reduce to valid links if any of the attributes "
                "'operators', 'id' is missing!"
            ) from e

        updated_links: list[WorkflowLinkFrontendDto] = []

        for link in links:
            if workflow_id in (link.from_operator, link.to_operator):
                # links from/to inputs/outputs will be dealt with in the clean_up_io_links validator
                updated_links.append(link)
            else:
                link_start_type = get_link_start_type_from_operator(link, operators)
                link_end_type = get_link_end_type_from_operator(link, operators)
                if (
                    link_start_type is not None
                    and link_end_type is not None
                    and (
                        link_start_type == link_end_type  # noqa: PLR1714
                        or link_start_type == DataType.Any
                        or link_end_type == DataType.Any
                    )
                ):
                    updated_links.append(link)

        return updated_links

    @validator("links", each_item=False)
    def links_acyclic_directed_graph(
        cls, links: list[WorkflowLinkFrontendDto], values: dict
    ) -> list[WorkflowLinkFrontendDto]:
        try:
            workflow_id = values["id"]
        except KeyError as e:
            raise ValueError(
                "Cannot check if links are acyclic if the attribute 'id' is missing!"
            ) from e

        indegrees: dict[UUID, int] = {}
        edges: list[tuple[UUID, UUID]] = []

        def add_edge(edge: tuple[UUID, UUID]) -> None:
            edges.append(edge)
            from_vertex = edge[0]
            to_vertex = edge[1]
            if from_vertex not in indegrees:
                indegrees[from_vertex] = 0
            if to_vertex not in indegrees:
                indegrees[to_vertex] = 1
            else:
                indegrees[to_vertex] = indegrees[to_vertex] + 1

        def remove_outgoing_edges(from_vertex: UUID) -> None:
            remove_edges: list[tuple[UUID, UUID]] = []
            for edge in edges:
                if edge[0] == from_vertex:
                    if indegrees[edge[1]] > 0:
                        indegrees[edge[1]] = indegrees[edge[1]] - 1
                    remove_edges.append(edge)
            del indegrees[from_vertex]

            for edge in remove_edges:
                edges.remove(edge)

        def vertices_with_indegree_zero() -> list[UUID]:
            return [vertex for vertex, indegree in indegrees.items() if indegree == 0]

        for link in links:
            from_operator = link.from_operator
            to_operator = link.to_operator
            if from_operator == workflow_id:
                from_operator = link.from_connector
            if to_operator == workflow_id:
                to_operator = link.to_connector
            add_edge((from_operator, to_operator))

        while len(vertices_with_indegree_zero()) > 0:
            vertex = vertices_with_indegree_zero()[0]
            remove_outgoing_edges(vertex)

        if len(edges) > 0:
            raise ValueError("Links may not form any loop!")

        return links

    @validator("inputs", each_item=False)
    def determine_inputs_from_operators_and_links(
        cls, inputs: list[WorkflowIoFrontendDto], values: dict
    ) -> list[WorkflowIoFrontendDto]:
        try:
            operators = values["operators"]
            links = values["links"]
            workflow_id = values["id"]
        except KeyError as e:
            raise ValueError(
                "Cannot determine inputs if any of the attributes "
                "'operators', 'links', 'id' is missing!"
            ) from e

        updated_inputs: list[WorkflowIoFrontendDto] = []

        for operator in operators:
            for connector in operator.inputs:
                if not is_link_end(
                    operator.id, connector.id, links, workflow_id
                ) or is_connected_to_input(operator.id, connector.id, inputs):
                    updated_inputs.append(
                        get_or_create_input(operator.id, connector.id, connector.type, inputs)
                    )

        return updated_inputs

    @validator("outputs", each_item=False)
    def determine_outputs_from_operators_and_links(
        cls, outputs: list[WorkflowIoFrontendDto], values: dict
    ) -> list[WorkflowIoFrontendDto]:
        try:
            operators = values["operators"]
            links = values["links"]
            workflow_id = values["id"]
        except KeyError as e:
            raise ValueError(
                "Cannot determine outputs if any of the attributes "
                "'operators', 'links', 'id' is missing!"
            ) from e

        updated_outputs: list[WorkflowIoFrontendDto] = []

        for operator in operators:
            for connector in operator.outputs:
                if not is_link_start(
                    operator.id, connector.id, links, workflow_id
                ) or is_connected_to_output(operator.id, connector.id, outputs):
                    updated_outputs.append(
                        get_or_create_output(operator.id, connector.id, connector.type, outputs)
                    )

        return updated_outputs

    @validator("inputs", "outputs", each_item=False)
    def io_names_none_or_unique(
        cls, ios: list[WorkflowIoFrontendDto]
    ) -> list[WorkflowIoFrontendDto]:
        ios_with_name = [io for io in ios if not (io.name is None or io.name == "")]

        names_unique(cls, ios_with_name)

        return ios

    @validator("inputs", "outputs", each_item=True)
    def name_or_constant_data_provided(
        cls, io: WorkflowIoFrontendDto, values: dict
    ) -> WorkflowIoFrontendDto:
        if values["state"] != State.RELEASED:
            return io

        if not (io.name is None or io.name == "") and io.constant:
            msg = (
                f"If name is specified ({io.name}) "
                f"constant must be false for input/output {io.id}"
            )
            raise ValueError(msg)
        if (io.name is None or io.name == "") and (
            not io.constant or io.constant_value is None or io.constant_value["value"] == ""
        ):
            msg = "Either name or constant data must be provided for input/output {io.id}"
            raise ValueError(msg)

        return io

    @root_validator()
    def clean_up_io_links(cls, values: dict) -> dict:
        try:
            operators = values["operators"]
            links = values["links"]
            inputs = values["inputs"]
            outputs = values["outputs"]
            workflow_id = values["id"]
        except KeyError as e:
            raise ValueError(
                "Cannot clean up io links if any of the attributes "
                "'operators', 'links', 'input', 'outputs', 'id' is missing!"
            ) from e

        updated_links: list[WorkflowLinkFrontendDto] = []

        for link in links:
            if not workflow_id in (link.from_operator, link.to_operator):
                # link has been checked in the reduce_to_valid_links validator already
                updated_links.append(link)
            elif link.from_operator == workflow_id:
                link_start_type = get_link_start_type_from_input(link, inputs)
                link_end_type = get_link_end_type_from_operator(link, operators)
                io_name = get_input_name_from_link(link, inputs)
                if (
                    link_start_type is not None
                    and link_end_type is not None
                    and (
                        link_start_type == link_end_type
                        or DataType.Any in (link_start_type, link_end_type)
                    )
                    and not (io_name is None or io_name == "")
                ):
                    updated_links.append(link)
            else:  # link.to_operator == workflow_id:
                link_start_type = get_link_start_type_from_operator(link, operators)
                link_end_type = get_link_end_type_from_output(link, outputs)
                io_name = get_output_name_from_link(link, outputs)
                if (
                    link_start_type is not None
                    and link_end_type is not None
                    and (
                        link_start_type == link_end_type
                        or DataType.Any in (link_start_type, link_end_type)
                    )
                    and not (io_name is None or io_name == "")
                ):
                    updated_links.append(link)

        # frontend sends link in put-request if input/output is named
        # -> no need to create links

        values["links"] = updated_links

        return values

    def get_from_connector_for_link(
        self,
        link: WorkflowLinkFrontendDto,
    ) -> ConnectorFrontendDto:
        from_connector_list: list[ConnectorFrontendDto] = []

        if link.from_operator == self.id:
            for inp in self.inputs:
                if inp.id == link.from_connector:
                    if inp.constant:
                        from_connector_list.append(
                            ConnectorFrontendDto(
                                id=inp.id,
                                name=None,
                                type=inp.type,
                                posX=inp.pos_x,
                                posY=inp.pos_y,
                            )
                        )
                    else:
                        from_connector_list.append(
                            ConnectorFrontendDto(
                                id=inp.id,
                                name=inp.name,
                                type=inp.type,
                                posX=inp.pos_x,
                                posY=inp.pos_y,
                            )
                        )
        else:
            for operator in self.operators:
                if operator.id == link.from_operator:
                    for connector in operator.outputs:
                        if connector.id == link.from_connector:
                            from_connector_list.append(connector)

        if len(from_connector_list) != 1:
            msg = (
                f"found {str(len(from_connector_list))} starts for link {link.id}:\n"
                f"{from_connector_list}\n"
            )
            raise ValueError(msg)

        return from_connector_list[0]

    def get_to_connector_for_link(
        self,
        link: WorkflowLinkFrontendDto,
    ) -> ConnectorFrontendDto:
        to_connector_list: list[ConnectorFrontendDto] = []

        if link.to_operator == self.id:
            for output in self.outputs:
                if output.id == link.to_connector:
                    to_connector_list.append(
                        ConnectorFrontendDto(
                            id=output.id,
                            name=output.name,
                            type=output.type,
                            posX=output.pos_x,
                            posY=output.pos_y,
                        )
                    )
        else:
            for operator in self.operators:
                if operator.id == link.to_operator:
                    for connector in operator.inputs:
                        if connector.id == link.to_connector:
                            to_connector_list.append(connector)

        if len(to_connector_list) != 1:
            msg = (
                f"found {str(len(to_connector_list))} ends for link {link.id}:\n"
                f"{to_connector_list}\n"
                f"{link}\n"
            )
            raise ValueError(msg)

        return to_connector_list[0]

    def additional_links_for_constant_inputs(self) -> list[Link]:
        link_list: list[Link] = []

        for inp in self.inputs:
            if inp.constant:
                link_dto = WorkflowLinkFrontendDto(
                    id=inp.id,
                    fromOperator=self.id,
                    fromConnector=inp.id,
                    toOperator=inp.operator,
                    toConnector=inp.connector,
                )
                try:
                    to_connector = self.get_to_connector_for_link(link_dto)
                    link_list.append(
                        link_dto.to_link(
                            ConnectorFrontendDto(
                                id=inp.id,
                                name=None,
                                type=inp.type,
                                posX=inp.pos_x,
                                posY=inp.pos_y,
                            ),
                            to_connector,
                            self.id,
                        )
                    )
                except ValueError:
                    if self.state != State.RELEASED:
                        pass

        return link_list

    def to_workflow_content(self) -> WorkflowContent:
        return WorkflowContent(
            inputs=[
                inp.to_workflow_content_io(
                    *get_operator_and_connector_name(inp.operator, inp.connector, self.operators)
                )
                for inp in self.inputs
                if not inp.constant and inp.name is not None
            ],
            constants=[
                inp.to_constant(
                    *get_operator_and_connector_name(inp.operator, inp.connector, self.operators)
                )
                for inp in self.inputs
                if inp.constant
            ],
            outputs=[
                output.to_workflow_content_io(
                    *get_operator_and_connector_name(
                        output.operator, output.connector, self.operators
                    )
                )
                for output in self.outputs
                if output.name is not None
            ],
            operators=[operator.to_operator() for operator in self.operators],
            links=[
                link.to_link(
                    self.get_from_connector_for_link(link),
                    self.get_to_connector_for_link(link),
                    self.id,
                )
                for link in self.links
            ]
            + self.additional_links_for_constant_inputs(),
        )

    def to_transformation_revision(
        self, documentation: str = "", timestamp: datetime | None = None
    ) -> TransformationRevision:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        return TransformationRevision(
            id=self.id,
            revision_group_id=self.group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            version_tag=self.tag,
            released_timestamp=timestamp
            if self.state in (State.RELEASED, State.DISABLED)
            else None,
            disabled_timestamp=timestamp if self.state == State.DISABLED else None,
            state=self.state,
            type=self.type,
            documentation=documentation,
            io_interface=IOInterface(
                inputs=[inp.to_io() for inp in self.inputs if not inp.constant],
                outputs=[output.to_io() for output in self.outputs],
            ),
            content=self.to_workflow_content(),
            test_wiring=self.wirings[0].to_wiring() if len(self.wirings) > 0 else WorkflowWiring(),
        )

    @classmethod
    def from_transformation_revision(
        cls, transformation_revision: TransformationRevision
    ) -> "WorkflowRevisionFrontendDto":
        assert isinstance(  # noqa: S101
            transformation_revision.content, WorkflowContent
        )  # hint for mypy

        inputs: list[WorkflowIoFrontendDto] = []

        for dynamic_wf_input in transformation_revision.content.inputs:
            inputs.append(WorkflowIoFrontendDto.from_workflow_content_io(dynamic_wf_input))
        for constant_wf_input in transformation_revision.content.constants:
            inputs.append(
                WorkflowIoFrontendDto.from_workflow_content_constant_input(constant_wf_input)
            )

        outputs: list[WorkflowIoFrontendDto] = []
        for output in transformation_revision.content.outputs:
            outputs.append(WorkflowIoFrontendDto.from_workflow_content_io(output))

        return WorkflowRevisionFrontendDto(
            id=transformation_revision.id,
            groupId=transformation_revision.revision_group_id,
            name=transformation_revision.name,
            description=transformation_revision.description,
            category=transformation_revision.category,
            type=transformation_revision.type,
            state=transformation_revision.state,
            tag=transformation_revision.version_tag,
            operators=[
                WorkflowOperatorFrontendDto.from_operator(operator)
                for operator in transformation_revision.content.operators
            ],
            inputs=inputs,
            outputs=outputs,
            links=[
                WorkflowLinkFrontendDto.from_link(link, transformation_revision.id)
                for link in transformation_revision.content.links
                if link.start.connector.id
                not in [constant.id for constant in transformation_revision.content.constants]
            ],
            wirings=[
                WiringFrontendDto.from_wiring(
                    transformation_revision.test_wiring, transformation_revision.id
                )
            ]
            if not (
                transformation_revision.test_wiring.input_wirings == []
                and transformation_revision.test_wiring.output_wirings == []
            )
            else [],
        )

    class Config:
        arbitrary_types_allowed = True
