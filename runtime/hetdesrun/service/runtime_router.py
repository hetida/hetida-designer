# -*- coding: utf-8 -*-
from typing import Optional, Dict
import traceback
import logging

from fastapi import APIRouter

from fastapi.encoders import jsonable_encoder


from hetdesrun import VERSION

from hetdesrun.component.code import update_code, check_parameter_names
from hetdesrun.component.load import check_importability
from hetdesrun.runtime.engine.plain.parsing import (
    parse_workflow_input,
    WorkflowParsingException,
)

from hetdesrun.datatypes import NamedDataTypedValue

from hetdesrun.models.base import VersionInfo
from hetdesrun.models.run import WorkflowExecutionInput, WorkflowExecutionResult
from hetdesrun.models.code import (
    CodeBody,
    GeneratedCode,
    CodeCheckResult,
    ComponentInfo,
)

from hetdesrun.runtime.context import execution_context

from hetdesrun.runtime import RuntimeExecutionError
from hetdesrun.runtime.engine.plain import workflow_execution_plain

from hetdesrun.runtime.engine.plain.workflow import obtain_all_nodes
from hetdesrun.runtime.service import runtime_service

from hetdesrun.wiring import (
    resolve_and_load_data_from_wiring,
    resolve_and_send_data_from_wiring,
)

from hetdesrun.adapters import AdapterHandlingException

from hetdesrun.utils import model_to_pretty_json_str

from hetdesrun.webservice.auth_dependency import get_auth_deps


logger = logging.getLogger(__name__)

runtime_router = APIRouter(tags=["runtime"])


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


@runtime_router.post(
    "/codegen",
    response_model=GeneratedCode,
    dependencies=get_auth_deps(),
)
async def codegen_service(
    codegen_input: CodeBody,
) -> GeneratedCode:
    """Service for generating and updating code stubs"""
    logger.info("CODEGEN INPUT JSON:\n%s", model_to_pretty_json_str(codegen_input))
    return GeneratedCode(
        code=update_code(
            existing_code=codegen_input.code,
            component_info=ComponentInfo.from_code_body(codegen_input),
        )
    )


@runtime_router.post(
    "/codecheck",
    response_model=CodeCheckResult,
    dependencies=get_auth_deps(),
)
async def codecheck_service(codecheck_input: CodeBody) -> CodeCheckResult:
    """Service for checking code of components"""

    logger.info("CODECHECK INPUT JSON:\n%s", model_to_pretty_json_str(codecheck_input))

    return_dict: Dict[str, Optional[str]] = {}

    result, possible_exception = check_importability(
        codecheck_input.code, codecheck_input.function_name
    )

    inputs_outputs_okay = check_parameter_names(
        [i.name for i in codecheck_input.inputs]
        + [o.name for o in codecheck_input.outputs]
    )

    return_dict = {"result": "ok" if result and inputs_outputs_okay else "failure"}

    if not result:
        return_dict["error"] = (
            str(possible_exception) if possible_exception is not None else None
        )
        return_dict["traceback"] = (
            str(possible_exception.__traceback__)
            if possible_exception is not None
            else None
        )
    elif not inputs_outputs_okay:
        return_dict[
            "error"
        ] = "Inputs/Outputs contain names not satisfying Python identifier rules"

    return CodeCheckResult(**return_dict)
