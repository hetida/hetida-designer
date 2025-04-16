import logging
from typing import Any

import msgspec
from fastapi.responses import JSONResponse

from hetdesrun import VERSION
from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import (
    UnitTestPayload,
    UnitTestResults,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.runtime.service import runtime_service, unittest_service
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)

runtime_router = HandleTrailingSlashAPIRouter(tags=["runtime"])


class MsgSpecJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)


@runtime_router.post(
    "/runtime",
    response_model=WorkflowExecutionResult,
    dependencies=get_auth_deps(),
)
async def runtime_endpoint(
    runtime_input: WorkflowExecutionInput,
) -> MsgSpecJSONResponse:
    return MsgSpecJSONResponse(
        content=(await runtime_service(runtime_input)).model_dump(mode="json")
    )


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
    return await unittest_service(payload.component_code)
