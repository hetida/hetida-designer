"""Correctness guards for the raw (``msgspec.Raw``-splicing) runtime-result serialization.

``encode_workflow_execution_result`` replaces the old ``model_dump(mode="json")`` path, which parsed
pandas' own JSON output back with ``json.loads`` only to have it re-encoded by msgspec. The raw
variant instead splices the bytes pandas produced straight into the response via ``msgspec.Raw``.

These tests pin that the new encoder:

* produces output **equivalent** to the old dump path across all payload types (the wire format must
  not change),
* keeps the metadata wrapper (``__hd_wrapped_data_object__`` / ``__metadata__`` / ``__data__`` /
  ``__data_parsing_options__``) intact so the parse side is unaffected,
* round-trips pandas payloads back into equal objects,
* coerces non-pandas outputs exactly as pydantic did (e.g. ``numpy`` scalars serialize, ``ndarray``
  does not), and
* still turns a non-serializable output into a structured failure result instead of raising.
"""

import json

import msgspec
import numpy as np
import pandas as pd

from hdutils import DataType
from hetdesrun.backend.models.info import ExecutionResponseFrontendDto
from hetdesrun.models.run import ProcessStage, WorkflowExecutionResult
from hetdesrun.service.serialization_helpers import (
    encode_workflow_execution_result,
    handle_frontend_exec_response_dict_serialisation,
    handle_workflow_execution_dict_serialisation,
)

JOB_ID = "00000000-0000-0000-0000-000000000001"
TR_ID = "00000000-0000-0000-0000-000000000002"


def _make_result(
    outputs: dict, types: dict[str, DataType], result: str = "ok"
) -> WorkflowExecutionResult:
    return WorkflowExecutionResult(
        result=result,
        output_types_by_output_name=types,
        output_results_by_output_name=outputs,
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )


def _decode_new(res: WorkflowExecutionResult) -> dict:
    return msgspec.json.decode(encode_workflow_execution_result(res))


def _decode_old(res: WorkflowExecutionResult) -> dict:
    """The previous path: pydantic ``model_dump(mode="json")`` then a msgspec encode."""
    return msgspec.json.decode(
        msgspec.json.encode(handle_workflow_execution_dict_serialisation(res))
    )


def _without_send_timestamp(decoded: dict) -> dict:
    # This stamp is taken at encode time and differs between the two calls by construction.
    decoded["measured_steps"]["runtime_sending_response_start"]["start"] = None
    return decoded


def _mixed_outputs() -> tuple[dict, dict[str, DataType]]:
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [4, 5, 6]})
    df.attrs = {"unit": "kW"}

    series = pd.Series([1.0, np.nan], index=["x", "x"])  # duplicate index
    series.attrs = {"meta": 1}

    mts = pd.DataFrame(
        {
            "metric": ["m1", "m1"],
            "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
            "value": [1.0, np.nan],
        }
    )

    sts = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
            "value": [1.0, np.nan],
            "state": ["ok", None],
        }
    )
    sts.attrs = {"dataset_metadata": {"single_metric": "m1"}}

    outputs = {
        "out_df": df,
        "out_series": series,
        "out_mts": mts,
        "out_sts": sts,
        "out_int": 42,
        "out_str": "hello",
        "out_bool": True,
        "out_float64": np.float64(3.14),  # pydantic coerces this; msgspec alone would not
        "out_plot": {"data": [{"x": [1, 2], "y": [1.0, None]}], "layout": {}},
        "out_any": {"k": [1, 2, 3]},
        "out_none": None,
    }
    types = {
        "out_df": DataType.DataFrame,
        "out_series": DataType.Series,
        "out_mts": DataType.MultiTSFrame,
        "out_sts": DataType.SingleTSFrame,
        "out_int": DataType.Integer,
        "out_str": DataType.String,
        "out_bool": DataType.Boolean,
        "out_float64": DataType.Float,
        "out_plot": DataType.PlotlyJson,
        "out_any": DataType.Any,
        "out_none": DataType.Any,
    }
    return outputs, types


def test_raw_encoding_matches_the_old_dump_path() -> None:
    outputs, types = _mixed_outputs()

    old = _without_send_timestamp(_decode_old(_make_result(outputs, types)))
    new = _without_send_timestamp(_decode_new(_make_result(outputs, types)))

    assert new == old


def test_metadata_wrapper_is_preserved() -> None:
    df = pd.DataFrame({"a": [1.0, 2.0]})
    df.attrs = {"unit": "kW"}
    series = pd.Series([1.0, 2.0])

    decoded = _decode_new(
        _make_result(
            {"df": df, "s": series},
            {"df": DataType.DataFrame, "s": DataType.Series},
        )
    )
    df_out = decoded["output_results_by_output_name"]["df"]
    s_out = decoded["output_results_by_output_name"]["s"]

    assert df_out["__hd_wrapped_data_object__"] == "DATAFRAME"
    assert df_out["__metadata__"] == {"unit": "kW"}
    assert df_out["__data__"] == {"a": {"0": 1.0, "1": 2.0}}
    assert s_out["__hd_wrapped_data_object__"] == "SERIES"
    assert s_out["__data_parsing_options__"] == {"orient": "split"}


def test_dataframe_payload_roundtrips_back_to_equal_object() -> None:
    df = pd.DataFrame({"a": [1.0, np.nan, 3.0], "b": [10, 20, 30]})
    df.attrs = {"unit": "kW"}

    decoded = _decode_new(_make_result({"df": df}, {"df": DataType.DataFrame}))

    # Re-validate through the model exactly as a consumer would (result_validation default True):
    # the __data__ wrapper is parsed back into a DataFrame.
    reparsed = WorkflowExecutionResult.model_validate(decoded)
    df_back = reparsed.output_results_by_output_name["df"]

    assert isinstance(df_back, pd.DataFrame)
    assert df_back.attrs == {"unit": "kW"}
    pd.testing.assert_frame_equal(df_back, df, check_dtype=False)


def test_numpy_array_output_still_fails_like_the_old_path() -> None:
    # An ndarray inside an ANY output is not JSON-serializable - pydantic could not dump it either,
    # so both paths must produce a structured failure, not a hard error.
    res = _make_result({"out_any": np.array([1.0, 2.0])}, {"out_any": DataType.Any})

    decoded = _decode_new(res)

    assert decoded["result"] == "failure"
    assert decoded["error"]["process_stage"] == "SERIALIZING_EXEC_RESULT"


def test_plotly_dict_with_injected_numpy_is_coerced_like_the_old_path() -> None:
    # A plotly output is arbitrary user-component code output. A coercible exotic (numpy float)
    # buried in it must still be coerced - now inside the single enc_hook encode pass - exactly as
    # the old pydantic dump did, without a separate pre-walk.
    plot = {
        "data": [{"x": [1, 2, 3], "y": [1.0, None, 3.0]}],
        "layout": {"title": "t"},
        "config": {},
        "meta": {"threshold": np.float64(0.5)},
    }
    res_args = ({"plot": plot}, {"plot": DataType.PlotlyJson})

    new = _without_send_timestamp(_decode_new(_make_result(*res_args)))
    old = _without_send_timestamp(_decode_old(_make_result(*res_args)))

    assert new["output_results_by_output_name"]["plot"]["meta"]["threshold"] == 0.5
    assert new == old


def test_plotly_dict_with_non_serializable_value_becomes_failure() -> None:
    # The guard must still fire for untrusted plotly output: a non-serializable value nested in the
    # figure dict yields a structured failure, not a crashed response.
    class NotJson:
        pass

    plot = {"data": [{"y": [1.0, 2.0]}], "layout": {"onclick": NotJson()}}
    decoded = _decode_new(_make_result({"plot": plot}, {"plot": DataType.PlotlyJson}))

    assert decoded["result"] == "failure"
    assert decoded["error"]["process_stage"] == "SERIALIZING_EXEC_RESULT"


def test_non_serializable_object_becomes_structured_failure() -> None:
    class NotJson:
        pass

    res = _make_result({"out_any": NotJson()}, {"out_any": DataType.Any})

    decoded = _decode_new(res)

    assert decoded["result"] == "failure"
    assert decoded["error"]["process_stage"] == "SERIALIZING_EXEC_RESULT"
    # The sending-response timestamp is still stamped even on the error path.
    assert decoded["measured_steps"]["runtime_sending_response_start"]["start"] is not None


def test_pathological_user_output_never_escapes_as_an_error() -> None:
    # Untrusted component output must never make serialization raise (which would surface as a 5xx);
    # every such case becomes a structured failure. Covers a circular reference (RecursionError) and
    # an unencodable dict key - both would otherwise escape the encoder.
    circular: dict = {}
    circular["self"] = circular

    cases = [
        ("circular ref in ANY", {"o": circular}, DataType.Any),
        ("circular ref in PLOTLYJSON", {"o": {"data": circular}}, DataType.PlotlyJson),
        ("unencodable dict key", {"o": {(1, 2): "x"}}, DataType.Any),
    ]
    for label, outputs, dtype in cases:
        # Must not raise (the guard catches it); must report a structured serialization failure.
        decoded = _decode_new(_make_result(outputs, dict.fromkeys(outputs, dtype)))
        assert decoded["result"] == "failure", label
        assert decoded["error"]["process_stage"] == "SERIALIZING_EXEC_RESULT", label


# --- backend -> caller boundary (ExecutionResponseFrontendDto) ---------------------------------
# The same guard must hold at the frontend boundary, which is where a combined backend+runtime
# service serializes live user output. ``infer_naive_result_serialization=False`` forces that
# (non-naive) path deterministically, independent of the is_runtime_service config.


def _make_frontend_dto(outputs: dict, types: dict) -> ExecutionResponseFrontendDto:
    return ExecutionResponseFrontendDto(
        result="success",
        output_results_by_output_name=outputs,
        output_types_by_output_name=types,
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )


def test_frontend_boundary_guards_pathological_output_as_structured_failure() -> None:
    circular: dict = {}
    circular["self"] = circular

    cases = [
        ("plain non-serializable", {"o": object()}, {"o": "ANY"}),
        ("circular ref in ANY", {"o": circular}, {"o": "ANY"}),
        ("circular ref in PLOTLYJSON", {"o": {"data": circular}}, {"o": "PLOTLYJSON"}),
    ]
    for label, outputs, types in cases:
        # Must not raise, must yield result="failure", and the dict must still msgspec-encode
        # (that is what the routers / kafka / callback path do next).
        decoded = handle_frontend_exec_response_dict_serialisation(
            _make_frontend_dto(outputs, types), infer_naive_result_serialization=False
        )
        assert decoded["result"] == "failure", label
        assert decoded["error"]["process_stage"] == "SERIALIZING_EXEC_RESULT", label
        assert msgspec.json.encode(decoded), label


def test_relay_splices_raw_output_verbatim() -> None:
    # When the result was relayed from a separate runtime, the output payload is carried on
    # the DTO as raw JSON bytes and must be spliced verbatim into the caller response - not parsed
    # and re-encoded. The model's own output field stays empty.
    raw_outputs = msgspec.json.encode({"plot": {"data": [1, 2, 3]}, "n": 100})
    dto = ExecutionResponseFrontendDto(
        result="ok",
        output_results_by_output_name={},
        output_types_by_output_name={"plot": "PLOTLYJSON", "n": "INT"},
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )
    dto.raw_output_results_json = raw_outputs

    dict_like = handle_frontend_exec_response_dict_serialisation(
        dto, infer_naive_result_serialization=True
    )

    # The spliced value is a msgspec.Raw placeholder; it encodes back to exactly the runtime bytes.
    assert isinstance(dict_like["output_results_by_output_name"], msgspec.Raw)
    decoded = msgspec.json.decode(msgspec.json.encode(dict_like))
    assert decoded["output_results_by_output_name"] == {"plot": {"data": [1, 2, 3]}, "n": 100}


def test_materialized_dump_decodes_relayed_outputs_for_non_msgspec_consumers() -> None:
    # Consumers that store / re-serialize the result outside the msgspec path (e.g. the scheduling
    # result persisted in a JSON db column via json.dumps) cannot handle a msgspec.Raw splice and
    # would lose the relayed outputs on a plain model_dump (empty model field + excluded raw field).
    # model_dump_with_materialized_outputs must decode the raw payload into plain python objects.
    raw_outputs = msgspec.json.encode({"plot": {"data": [1, 2, 3]}, "n": 100})
    dto = ExecutionResponseFrontendDto(
        result="ok",
        output_results_by_output_name={},
        output_types_by_output_name={"plot": "PLOTLYJSON", "n": "INT"},
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )
    dto.raw_output_results_json = raw_outputs

    dumped = dto.model_dump_with_materialized_outputs()

    assert dumped["output_results_by_output_name"] == {"plot": {"data": [1, 2, 3]}, "n": 100}
    # Must survive a plain json.dumps round-trip (that is what a JSON db column does): no Raw leaks.
    assert json.loads(json.dumps(dumped))["output_results_by_output_name"] == {
        "plot": {"data": [1, 2, 3]},
        "n": 100,
    }


def test_materialized_dump_without_relay_matches_plain_dump() -> None:
    # Same-service case: outputs already live on the model field, so behaviour is unchanged.
    dto = ExecutionResponseFrontendDto(
        result="ok",
        output_results_by_output_name={"output": "test"},
        output_types_by_output_name={"output": "STRING"},
        job_id=JOB_ID,
        tr_id=TR_ID,
        tr_name="t",
        tr_tag="1.0.0",
    )

    assert dto.model_dump_with_materialized_outputs() == dto.model_dump(mode="json")
    assert dto.model_dump_with_materialized_outputs()["output_results_by_output_name"] == {
        "output": "test"
    }


def test_frontend_from_exception_builds_a_complete_failure_dto() -> None:
    # Regression guard: the DTO must override from_exception so the serialization-failure fallback
    # carries the required ``result`` field (the inherited base method omitted it).
    dto = ExecutionResponseFrontendDto.from_exception(
        ValueError("boom"),
        ProcessStage.SERIALIZING_EXEC_RESULT,
        JOB_ID,
        tr_name="t",
        tr_tag="1.0.0",
        tr_id=TR_ID,
    )
    assert isinstance(dto, ExecutionResponseFrontendDto)
    assert dto.result == "failure"
    assert dto.error is not None
