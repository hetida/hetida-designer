import logging
from typing import Any, Dict

from hetdesrun.runtime import (
    runtime_execution_logger,
)
from hetdesrun.runtime.engine.plain.workflow import Workflow
from hetdesrun.runtime.logging import execution_context_filter

logger = logging.getLogger(__name__)


logger.addFilter(execution_context_filter)
runtime_execution_logger.addFilter(execution_context_filter)


async def workflow_execution_plain(workflow: Workflow) -> Dict[str, Any]:
    res: Dict[str, Any] = await workflow.result
    return res
