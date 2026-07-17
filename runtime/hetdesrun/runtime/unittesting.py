import json
import os
import shutil
import subprocess  # nosec: B404
import tempfile
from pathlib import Path

import hetdesrun
from hetdesrun.models.code import CodeModule
from hetdesrun.models.component import ComponentRevision
from hetdesrun.models.run import UnitTestResults

UNITTESTING_CONFTEST_FILE_PATH = Path(__file__).parent / "unittesting_conftest.py"

COMPONENT_IMPORT_CONTEXT_FILE_NAME = "component_import_context.json"


def get_runtime_base_dir() -> Path:
    """Directory containing the hetdesrun package (and hdutils.py, hetdesrun_config.py)

    hetdesrun is not an installed package: it is importable in the runtime process
    only because this base directory is on the runtime process' sys.path.
    """
    return Path(hetdesrun.__file__).resolve().parent.parent


def unittest_code(
    component_code: str,
    code_modules: list[CodeModule] | None = None,
    components: list[ComponentRevision] | None = None,
) -> UnitTestResults:
    """Run pytest on the component code in a separate process

    Pytest cannot be run cleanly in the runtime process itself, so the component
    code is written into a temporary directory and a separate pytest process is
    run on it.

    code_modules and components should contain the code modules and component
    revisions of all components (transitively) imported via import_comp by the
    component code, analogously to ordinary execution. They are provided to the
    pytest process via a json file which is loaded by an accompanying conftest.py
    binding them into the execution context, making import_comp invocations in
    the component code work.
    """
    if code_modules is None:
        code_modules = []
    if components is None:
        components = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(os.path.join(tmp_dir, "test_component.py"), "w") as f:
            f.write(component_code)

        with open(os.path.join(tmp_dir, COMPONENT_IMPORT_CONTEXT_FILE_NAME), "w") as f:
            json.dump(
                {
                    "code_modules": [
                        json.loads(code_module.model_dump_json()) for code_module in code_modules
                    ],
                    "components": [
                        json.loads(component.model_dump_json()) for component in components
                    ],
                },
                f,
            )

        shutil.copy(UNITTESTING_CONFTEST_FILE_PATH, os.path.join(tmp_dir, "conftest.py"))

        # Make hetdesrun, hdutils and hetdesrun_config importable in the pytest
        # process despite it running in the temporary directory:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(get_runtime_base_dir()) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        env["LOGFIRE_IGNORE_NO_CONFIG"] = "1"

        completed_process = subprocess.run(  # noqa: S603 # nosec B603 B607
            ["pytest", "--doctest-modules", "."],  # noqa: S607
            cwd=tmp_dir,
            env=env,
            capture_output=True,
            check=False,  # we extract both stdout and stderr and let the user see everything
            # Hence we do not need to raise exceptions if the command status is != 0
        )
    return UnitTestResults(
        pytest_stdout_str=completed_process.stdout.decode("utf8"),
        pytest_stderr_str=completed_process.stderr.decode("utf8"),
    )
