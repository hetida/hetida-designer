from collections import deque
from typing import Any

from pydantic import Field

from hetdesrun.datatypes import DataType
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.run import WorkflowExecutionInfo
from hetdesrun.runtime.logging import SimplifiedLogRecord
from hetdesrun.webservice.config import get_config


class ExecutionResponseFrontendDto(WorkflowExecutionInfo):
    result: str
    output_results_by_output_name: dict[str, Any] = {}
    output_types_by_output_name: dict[str, DataType | None] = {}
    resolved_reproducibility_references: ReproducibilityReference = Field(
        default_factory=ReproducibilityReference,
        description="Resolved references to information needed to reproduce an execution result."
        "The provided data can be used to replace data that would usually be produced at runtime.",
    )
    process_id: int | None = Field(
        None,
        description=(
            "Process Id (PID) of the process handling the request, "
            "if advanced performance measuring is configured."
        ),
    )

    gathered_component_code_logs: deque[SimplifiedLogRecord] = deque(
        maxlen=get_config().user_component_code_logs_max_len
    )
