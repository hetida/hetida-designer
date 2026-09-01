import datetime
import logging

import logfire
from fastapi import Response

from hetdesrun import VERSION
from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import (
    UnitTestPayload,
    UnitTestResults,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.runtime.service import runtime_service, unittest_service
from hetdesrun.service.serialization_helpers import encode_workflow_execution_result
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)

runtime_router = HandleTrailingSlashAPIRouter(tags=["runtime"])


@runtime_router.post(
    "/runtime",
    response_model=WorkflowExecutionResult,
    dependencies=get_auth_deps(),
)
async def runtime_endpoint(
    runtime_input: WorkflowExecutionInput,
) -> Response:
    with logfire.span(
        "runtime execution request handling without fastapi parsing",
        trafo_id=str(runtime_input.trafo_id),
        job_id=str(runtime_input.job_id),
    ):
        received_backend_request = datetime.datetime.now(datetime.timezone.utc)
        result = await runtime_service(runtime_input)
        result.measured_steps.backend_calling_runtime_request_start.end = received_backend_request

        with logfire.span("runtime execution result serialization without fastapi"):
            # Raw-splicing encode using msgspec.Raw for e.g. Pandas ouput to avoid
            # multiple serialization loops, i.e. skipping the json.loads round-trip
            # + re-encode.
            response = Response(
                content=encode_workflow_execution_result(result),
                media_type="application/json",
            )

    return response


@runtime_router.get("/info", response_model=VersionInfo)
async def info_service() -> dict[str, str]:
    """Version Info Endpoint

    Unauthorized, may be used for readiness probes.
    """
    return {"version": VERSION}


@runtime_router.post(
    "/unittest",
    response_model=UnitTestResults,
    dependencies=get_auth_deps(),
)
async def unittest_component(
    payload: UnitTestPayload,
) -> UnitTestResults:
    return await unittest_service(payload)
