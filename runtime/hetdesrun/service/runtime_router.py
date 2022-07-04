# -*- coding: utf-8 -*-
import logging

from hetdesrun import VERSION
from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import WorkflowExecutionInput, WorkflowExecutionResult
from hetdesrun.runtime.service import runtime_service
from hetdesrun.webservice.auth_dependency import get_auth_deps
from hetdesrun.webservice.router import HandleTrailingSlashAPIRouter

logger = logging.getLogger(__name__)

runtime_router = HandleTrailingSlashAPIRouter(tags=["runtime"])


@runtime_router.post(
    "/runtime",
    response_model=WorkflowExecutionResult,
    dependencies=get_auth_deps(),
)
# pylint: disable=R0911
async def runtime_endpoint(
    runtime_input: WorkflowExecutionInput,
) -> WorkflowExecutionResult:
    return await runtime_service(runtime_input)


@runtime_router.get("/info", response_model=VersionInfo)
async def info_service() -> dict:
    """Version Info Endpoint

    Unauthorized, may be used for readiness probes.
    """
    return {"version": VERSION}
