import datetime
import logging

from hetdesrun import VERSION
from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import (
    UnitTestPayload,
    UnitTestResults,
    WorkflowExecutionInput,
    WorkflowExecutionResult,
)
from hetdesrun.runtime.service import runtime_service, unittest_service
from hetdesrun.service.serialization_helpers import (
    MsgSpecJSONResponse,
    handle_workflow_execution_dict_serialisation,
)
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
) -> MsgSpecJSONResponse:
    received_backend_request = datetime.datetime.now(datetime.timezone.utc)
    result = await runtime_service(runtime_input)
    result.measured_steps.backend_calling_runtime_request_start.end = received_backend_request

    dict_like_json_serializable_obj = handle_workflow_execution_dict_serialisation(result)

    dict_like_json_serializable_obj["measured_steps"]["runtime_sending_response_start"]["start"] = (
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    return MsgSpecJSONResponse(content=dict_like_json_serializable_obj)


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
