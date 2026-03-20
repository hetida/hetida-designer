from typing import Any

import msgspec
from fastapi.responses import JSONResponse
from pydantic_core import PydanticSerializationError, PydanticSerializationUnexpectedValue

from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.run import ProcessStage, WorkflowExecutionResult
from hetdesrun.webservice.config import get_config


class MsgSpecJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)


def handle_workflow_execution_dict_serialisation(wf_exec_result: WorkflowExecutionResult) -> dict:
    """Handling of dict conversion that cannot guarantee exception-free serialziation

    This occurs if output results for Any-like outputs (ANY, PLOTLYJSON) get a result
    Python object from the trafo execution, that is not json serializable. We cannot
    check that during validation since we want to actually allow arbitrary objects and
    we do not want to serialize at a previous step only to check serializability
    thereby introducing additional serialization which has negative performance
    impact, e.g. for large plots.
    """

    try:
        dict_like_json_serializable_obj = wf_exec_result.model_dump(mode="json")
    except (PydanticSerializationError, PydanticSerializationUnexpectedValue) as exc:
        wf_exec_result_with_serialization_errors = WorkflowExecutionResult.from_exception(
            exc,
            ProcessStage.SERIALIZING_EXEC_RESULT,
            wf_exec_result.job_id,
            tr_name=wf_exec_result.tr_name,
            tr_id=wf_exec_result.tr_id,
            tr_tag=wf_exec_result.tr_tag,
            measured_steps=wf_exec_result.measured_steps,
            mem_info=wf_exec_result.measured_steps.runtime_memory_info,
        )
        dict_like_json_serializable_obj = wf_exec_result_with_serialization_errors.model_dump(
            mode="json"
        )

    return dict_like_json_serializable_obj


def handle_frontend_exec_response_dict_serialisation(
    exec_resp_frontend_dto: ExecutionResponseFrontendDto,
    enforce_naive_result_serialization: bool = False,
    infer_naive_result_serialization: bool = True,
) -> dict:
    """Handling of dict conversion that cannot guarantee exception-free serialziation

    This occurs if output results for Any-like outputs (ANY, PLOTLYJSON) get a result
    Python object from the trafo execution, that is not json serializable. We cannot
    check that during validation since we want to actually allow arbitrary objects and
    we do not want to serialize at a previous step only to check serializability
    thereby introducing additional serialization which has negative performance
    impact, e.g. for large plots.

    This needs to be handled for the ExecutionResponseFrontendDto as well for
    running runtime and backend in same container/service.

    Furthermore this function handles the case of possibly second serialization
    of direct_provisioning output results:
    * If coming from a separate runtime service, the dict of output results
      has already undergone a serialization / deserialization step. It is now
      a correct json dict-like object, in particular Pandas results have the
      correct form. In particular the Pandas objects do not need to be parsed
      and serialized again!
    * Parsing the pandas object representations could lead to potentially unwanted
      effects as they are parsed via Pandas' read_json function which does for
      example datetime inference on strings.

    To mitigate these possibly unwanted effects this function infers from the setup
    whether parsing / serialization is necessary for the direct output data if
    infer_naive_result_serialization is True. naive result serialization can
    be enforced by setting enforce_naive_result_serialization to True.
    """

    use_naive_result_serialization = False  # default to ordinary serialization

    if infer_naive_result_serialization:
        use_naive_result_serialization = not get_config().is_runtime_service

    if enforce_naive_result_serialization:
        use_naive_result_serialization = True

    try:
        dict_like_json_serializable_obj = exec_resp_frontend_dto.model_dump(
            mode="json", context={"naive_result_serialization": use_naive_result_serialization}
        )

    except (PydanticSerializationError, PydanticSerializationUnexpectedValue) as exc:
        exec_resp_frontend_dto_with_serialization_errors = (
            ExecutionResponseFrontendDto.from_exception(
                exc,
                ProcessStage.SERIALIZING_EXEC_RESULT,
                exec_resp_frontend_dto.job_id,
                tr_name=exec_resp_frontend_dto.tr_name,
                tr_id=exec_resp_frontend_dto.tr_id,
                tr_tag=exec_resp_frontend_dto.tr_tag,
                measured_steps=exec_resp_frontend_dto.measured_steps,
                mem_info=exec_resp_frontend_dto.measured_steps.runtime_memory_info,
            )
        )
        dict_like_json_serializable_obj = (
            exec_resp_frontend_dto_with_serialization_errors.model_dump(mode="json")
        )

    return dict_like_json_serializable_obj
