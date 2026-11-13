"""Make import_comp work in the tests of base components importing other base components

The tests in the code of base components are run with pytest directly, e.g. by ./run check. In
contrast to executions and to tests run from the user interface, no component revisions are
provided to import_comp then. So when pytest collects a base component importing other
components, the base components are provided to import_comp, before pytest imports its code.
"""

import functools
import logging
from pathlib import Path
from typing import Any

from hetdesrun.component.load import prepare_component_import_context
from hetdesrun.trafoutils.io.load import load_transformation_revisions_from_directory
from hetdesrun.utils import Type

BASE_COMPONENTS_PATH = Path(__file__).parent / "transformations" / "components"


@functools.cache
def provide_base_components_for_import() -> None:
    load_logger = logging.getLogger("hetdesrun.trafoutils.io.load")
    level = load_logger.level
    # instead of logging each loaded file
    load_logger.setLevel(logging.WARNING)
    try:
        trafos, _ = load_transformation_revisions_from_directory(str(BASE_COMPONENTS_PATH))
    finally:
        load_logger.setLevel(level)
    components = [trafo for trafo in trafos.values() if trafo.type is Type.COMPONENT]
    prepare_component_import_context(
        [component.to_code_module() for component in components],
        [component.to_component_revision() for component in components],
    )


def pytest_collect_file(file_path: Path, parent: Any) -> None:  # noqa: ARG001
    if (
        file_path.suffix == ".py"
        and BASE_COMPONENTS_PATH in file_path.parents
        and "import_comp(" in file_path.read_text(encoding="utf8")
    ):
        provide_base_components_for_import()
