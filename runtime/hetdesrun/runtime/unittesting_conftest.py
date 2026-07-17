"""Conftest for unittesting component code via a separate pytest process

This file is copied as conftest.py into the temporary directory in which the
component code under test is run via pytest (see hetdesrun.runtime.unittesting).

Pytest imports conftest.py before collecting/importing the component code module.
Hence binding the code modules and component revisions of the (transitively)
imported components into the execution context here makes import_comp invocations
in the component code work exactly as during ordinary execution.
"""

import json
from pathlib import Path

from hetdesrun.component.load import prepare_component_import_context
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentRevision

component_import_context = json.loads(
    (Path(__file__).parent / "component_import_context.json").read_text(encoding="utf8")
)

prepare_component_import_context(
    [CodeModule.model_validate(cm) for cm in component_import_context["code_modules"]],
    [ComponentRevision.model_validate(c) for c in component_import_context["components"]],
)
