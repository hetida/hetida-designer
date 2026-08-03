from __future__ import annotations

from collections import deque
from typing import Any
from uuid import UUID

from pydantic import Field

from hetdesrun.datatypes import DataType
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.models.run import (
    AllMeasuredSteps,
    ProcessStage,
    RuntimeMemoryInfo,
    WorkflowExecutionInfo,
)
from hetdesrun.runtime.logging import SimplifiedLogRecord
from hetdesrun.webservice.config import get_config


class ExecutionResponseFrontendDto(WorkflowExecutionInfo):
    result: str
    output_results_by_output_name: dict[str, Any] = {}
    output_types_by_output_name: dict[str, DataType | None] = {}
    # Set only when the result was relayed from a *separate* runtime service: the raw JSON bytes of
    # output_results_by_output_name exactly as the runtime produced them. It lets the backend splice
    # that (already validated well-formed) payload into the response to the caller without parsing
    # and re-encoding it - see run_execution_input and the frontend serialization helper.
    # Excluded from serialization; the splice consumes it explicitly.
    raw_output_results_json: bytes | None = Field(default=None, exclude=True, repr=False)
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

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        process_stage: ProcessStage,
        job_id: UUID,
        tr_name: str,
        tr_tag: str,
        tr_id: UUID,
        cause: BaseException | None = None,
        measured_steps: AllMeasuredSteps | None = None,
        mem_info: RuntimeMemoryInfo | None = None,
    ) -> ExecutionResponseFrontendDto:
        """Build a structured failure DTO from an exception.

        The base ``WorkflowExecutionInfo.from_exception`` returns a base instance without the
        required ``result`` field; overriding here (as ``WorkflowExecutionResult`` does) ensures the
        serialization-failure fallback produces a valid ``ExecutionResponseFrontendDto`` with
        ``result="failure"`` rather than a response missing ``result``.
        """
        wf_exec_info = super().from_exception(
            exception,
            process_stage,
            job_id,
            tr_name=tr_name,
            tr_tag=tr_tag,
            tr_id=tr_id,
            cause=cause,
            measured_steps=measured_steps,
            mem_info=mem_info,
        )
        return cls(**wf_exec_info.model_dump(), result="failure")
