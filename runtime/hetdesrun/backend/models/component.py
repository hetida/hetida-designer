from datetime import datetime, timezone
from typing import Literal

from hetdesrun.backend.models.io import ConnectorFrontendDto
from hetdesrun.backend.models.transformation import TransformationRevisionFrontendDto
from hetdesrun.backend.models.wiring import WiringFrontendDto
from hetdesrun.models.wiring import WorkflowWiring
from hetdesrun.persistence.models.io import IOInterface
from hetdesrun.persistence.models.transformation import TransformationRevision
from hetdesrun.utils import State, Type


class ComponentRevisionFrontendDto(TransformationRevisionFrontendDto):
    type: Literal[Type.COMPONENT]  # noqa: A003
    code: str

    class Config:
        arbitrary_types_allowed = True

    def to_transformation_revision(self, documentation: str = "") -> TransformationRevision:
        return TransformationRevision(
            id=self.id,
            revision_group_id=self.group_id,
            name=self.name,
            description=self.description,
            category=self.category,
            version_tag=self.tag,
            released_timestamp=datetime.now(tz=timezone.utc)
            if self.state == State.RELEASED
            else None,
            disabled_timestamp=datetime.now(tz=timezone.utc)
            if self.state == State.DISABLED
            else None,
            state=self.state,
            type=self.type,
            documentation=documentation,
            io_interface=IOInterface(
                inputs=[inp.to_io() for inp in self.inputs],
                outputs=[output.to_io() for output in self.outputs],
            ),
            content=self.code,
            test_wiring=self.wirings[0].to_wiring() if len(self.wirings) > 0 else WorkflowWiring(),
        )

    @classmethod
    def from_transformation_revision(
        cls, transformation_revision: TransformationRevision
    ) -> "ComponentRevisionFrontendDto":
        assert isinstance(  # noqa: S101
            transformation_revision.content, str
        )  # hint for mypy
        return ComponentRevisionFrontendDto(
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
            code=transformation_revision.content,
        )
