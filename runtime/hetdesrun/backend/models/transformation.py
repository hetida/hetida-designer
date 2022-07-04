from datetime import datetime
from typing import List

# pylint: disable=no-name-in-module
from pydantic import validator

from hetdesrun.backend.models.info import BasicInformation
from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.models.util import names_unique
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.persistence.models.workflow import WorkflowContent
from hetdesrun.utils import State, Type


class TransformationRevisionFrontendDto(BasicInformation):
    inputs: List[ConnectorFrontendDto] = []
    outputs: List[ConnectorFrontendDto] = []
    wirings: List[WiringFrontendDto] = []

    # pylint: disable=no-self-argument,no-self-use
    @validator("inputs", "outputs", each_item=False)
    def input_names_none_or_unique(
        cls, ios: List[ConnectorFrontendDto]
    ) -> List[ConnectorFrontendDto]:
        ios_with_name = [io for io in ios if io.name is not None]

        names_unique(cls, ios_with_name)

        return ios

    def to_transformation_revision(
        self, documentation: str = ""
    ) -> TransformationRevision:
        return TransformationRevision(
            id=self.id,
            revision_group_id=self.group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            version_tag=self.tag,
            released_timestamp=datetime.now() if self.state == State.RELEASED else None,
            disabled_timestamp=datetime.now() if self.state == State.DISABLED else None,
            state=self.state,
            type=self.type,
            documentation=documentation,
            io_interface=IOInterface(
                inputs=[input.to_io() for input in self.inputs],
                outputs=[output.to_io() for output in self.outputs],
            ),
            content="" if self.type == Type.COMPONENT else WorkflowContent(),
            test_wiring=self.wirings[0].to_wiring()
            if len(self.wirings) > 0
            else WorkflowWiring(),
        )

    @classmethod
    def from_transformation_revision(
        cls, transformation_revision: TransformationRevision
    ) -> "TransformationRevisionFrontendDto":
        return TransformationRevisionFrontendDto(
            id=transformation_revision.id,
            groupId=transformation_revision.revision_group_id,
            name=transformation_revision.name,
            description=transformation_revision.description,
            category=transformation_revision.category,
            type=transformation_revision.type,
            state=transformation_revision.state,
            tag=transformation_revision.version_tag,
            inputs=[
                ConnectorFrontendDto.from_io(io)
                for io in transformation_revision.io_interface.inputs
            ],
            outputs=[
                ConnectorFrontendDto.from_io(io)
                for io in transformation_revision.io_interface.outputs
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
