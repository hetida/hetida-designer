import datetime
from typing import Any

import msgspec
from fastapi.responses import JSONResponse
from pydantic_core import (
    PydanticSerializationError,
    PydanticSerializationUnexpectedValue,
    to_jsonable_python,
)

from hdutils import DataType, serialize_output_results_raw
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.run import ProcessStage, WorkflowExecutionResult
from hetdesrun.webservice.config import get_config

# Field carrying the direct-provisioning output data; excluded from the pydantic dump and injected
# separately as raw-spliced JSON (see encode_workflow_execution_result).
_OUTPUT_RESULTS_FIELD = "output_results_by_output_name"

# Encoder for the runtime result. ``enc_hook=to_jsonable_python`` is msgspec's fallback for any
# value it cannot encode natively: it applies exactly pydantic's ``mode="json"`` coercion, but only
# to the leaves that need it - so a clean (plotly/ANY) output encodes in a single native pass with
# no pre-walk, while numpy scalars & co. are still coerced and genuinely non-serializable user
# output still raises (and is caught below).
_runtime_result_encoder = msgspec.json.Encoder(enc_hook=to_jsonable_python)


class ResultSerializationError(Exception):
    """The execution result, i.e. usually the result of a workflow output, cannot be serialized"""


# Results of these output types are serialized as they are, so they may contain arbitrary objects
_ARBITRARY_RESULT_DATA_TYPES = (DataType.Any, DataType.PlotlyJson)


def _explain_serialization_error(
    exc: Exception,
    output_results_by_output_name: dict[str, Any],
    output_types_by_output_name: dict[str, DataType | None],
) -> ResultSerializationError:
    """A ResultSerializationError with a clearer message than exc, caused by exc

    Only uses information at hand: the message of exc and the names, types and top-level Python
    types of the output results. It deliberately does not serialize anything again (e.g. output by
    output to find the failing one), so that the error path stays cheap, even if many executions
    fail at once. The traceback of exc is kept, so that the error location stays the same.
    """
    message = str(exc) or type(exc).__name__
    lines = [f"The execution result could not be serialized to JSON: {message}"]

    # Single values of these types are serializable, so only outputs with other results may fail
    candidate_types_by_output_name: dict[str, DataType | None] = {}
    for output_name, result in output_results_by_output_name.items():
        data_type = output_types_by_output_name.get(output_name)
        if (
            data_type in _ARBITRARY_RESULT_DATA_TYPES
            and result is not None
            and not isinstance(result, str | int | float | bool)
        ):
            candidate_types_by_output_name[output_name] = data_type
    if candidate_types_by_output_name:
        lines.append(
            "Results of ANY and PLOTLYJSON outputs are serialized as they are and must therefore"
            " consist of JSON serializable objects only. Outputs which may cause this error: "
            + ", ".join(
                f"'{output_name}' ({data_type})"
                for output_name, data_type in candidate_types_by_output_name.items()
            )
            + "."
        )
    if isinstance(exc, RecursionError):
        lines.append("This may be caused by an object containing itself or by very deep nesting.")
    if "<class 'pandas." in message and DataType.Any in candidate_types_by_output_name.values():
        lines.append(
            "Pandas Series and DataFrames are only serialized if they are the direct result of an"
            " ANY output itself, not if they are nested in an ANY output, e.g. in a dict or list."
        )

    explained = ResultSerializationError("\n".join(lines)).with_traceback(exc.__traceback__)
    explained.__cause__ = exc
    return explained


class MsgSpecJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)


def _set_runtime_sending_response_start(envelope: dict) -> None:
    """Stamp the moment right before the response goes out onto the wire"""
    envelope["measured_steps"]["runtime_sending_response_start"]["start"] = datetime.datetime.now(
        datetime.timezone.utc
    ).isoformat()


def encode_workflow_execution_result(wf_exec_result: WorkflowExecutionResult) -> bytes:
    """Encode a runtime execution result to JSON bytes, splicing pandas payloads as raw json bytes.

    The whole envelope (ids, wiring, measured steps, error, ...) is dumped with pydantic's
    ``model_dump(mode="json")`` *except* the direct-provisioning output data, which is built
    separately via ``serialize_output_results_raw`` so that pandas payloads become ``msgspec.Raw``.
    The merged dict is then encoded once with msgspec (``enc_hook=to_jsonable_python``): it splices
    the pandas json bytes verbatim and coerces any remaining untrusted output leaves in the same
    pass, avoiding the previous ``json.loads(df.to_json())`` round-trips.

    Output values are arbitrary user-component code output (this is especially the point for
    PLOTLYJSON, which is typically transported to the caller rather than through an adapter). Their
    serialization should therefore be guarded: *any* failure - a non-JSON-serializable object, a
    circular reference (``RecursionError``), an unencodable dict key, etc. - is turned into a
    structured failure result. Serialization should never surface as a 5xx from the runtime, so the
    guard is deliberately a broad ``except Exception`` and not a curated list of exception types.
    The error message names the outputs whose results may be the cause (without serializing again).
    """
    try:
        envelope = wf_exec_result.model_dump(mode="json", exclude={_OUTPUT_RESULTS_FIELD})
        envelope[_OUTPUT_RESULTS_FIELD] = serialize_output_results_raw(
            wf_exec_result.output_results_by_output_name,
            wf_exec_result.output_types_by_output_name,
        )
        _set_runtime_sending_response_start(envelope)
        return _runtime_result_encoder.encode(envelope)
    except Exception as exc:  # noqa: BLE001  # serialization of untrusted output should never 500
        error_result = WorkflowExecutionResult.from_exception(
            _explain_serialization_error(
                exc,
                wf_exec_result.output_results_by_output_name,
                wf_exec_result.output_types_by_output_name,
            ),
            ProcessStage.SERIALIZING_EXEC_RESULT,
            wf_exec_result.job_id,
            tr_name=wf_exec_result.tr_name,
            tr_id=wf_exec_result.tr_id,
            tr_tag=wf_exec_result.tr_tag,
            measured_steps=wf_exec_result.measured_steps,
            mem_info=wf_exec_result.measured_steps.runtime_memory_info,
        )
        # The error result carries no output data, so an ordinary dump encodes cleanly.
        envelope = error_result.model_dump(mode="json")
        _set_runtime_sending_response_start(envelope)
        return _runtime_result_encoder.encode(envelope)


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

    # Broad guard, mirroring encode_workflow_execution_result: when the runtime and backend run in
    # the same service the (non-naive) dump here serializes live, untrusted user-component output,
    # so *any* failure - non-serializable object, circular reference (RecursionError), unencodable
    # dict key, etc. - should become a structured failure result rather than a 5xx. (In the naive
    # case the data is already valid JSON from a separate runtime, so this dump cannot fail on it.)
    # The returned dict is downstream-encoded by msgspec; a successful mode="json" dump is
    # JSON-native, so that encode cannot fail either. The fallback dump serializes only
    # # runtime-controlled data.
    try:
        dict_like_json_serializable_obj = exec_resp_frontend_dto.model_dump(
            mode="json", context={"naive_result_serialization": use_naive_result_serialization}
        )

    except Exception as exc:  # noqa: BLE001  # serialization of untrusted output should never 500
        exec_resp_frontend_dto_with_serialization_errors = (
            ExecutionResponseFrontendDto.from_exception(
                _explain_serialization_error(
                    exc,
                    exec_resp_frontend_dto.output_results_by_output_name,
                    exec_resp_frontend_dto.output_types_by_output_name,
                ),
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

    # If the output data was relayed from a separate runtime as raw JSON bytes, splice
    # those bytes straight in (as msgspec.Raw) instead of the empty model field, so the payload is
    # not parsed and re-encoded on its way to the caller. Requires a msgspec encoder downstream (the
    # response classes and the kafka path use one); the raw guard already ran at decode time.
    if exec_resp_frontend_dto.raw_output_results_json is not None:
        dict_like_json_serializable_obj["output_results_by_output_name"] = msgspec.Raw(
            exec_resp_frontend_dto.raw_output_results_json
        )

    return dict_like_json_serializable_obj
