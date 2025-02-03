import inspect
import os
import subprocess
import tempfile

import hdutils
from hetdesrun.models.run import UnitTestResults


def unittest_code(component_code: str) -> UnitTestResults:
    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(os.path.join(tmp_dir, "test_component.py"), "w") as f:
            f.write(component_code)

        hdutils_code = inspect.getsource(hdutils)

        with open(os.path.join(tmp_dir, "hdutils.py"), "w") as f:
            f.write(hdutils_code)

        # TODO: What is with other hetdesrun imports in the component's code?
        # since we are in a different directory, we cannot import from hetdesrun.
        # maybe components should not do that in every case?

        completed_process = subprocess.run(  # noqa: S603
            ["pytest", "--doctest-modules", "."],  # noqa: S607
            cwd=tmp_dir,
            capture_output=True,
            check=False,  # we extract both stdout and stderr and let the user see everything
            # Hence we do not need to raise exceptions if the command status is != 0
        )
    return UnitTestResults(
        pytest_stdout_str=completed_process.stdout.decode("utf8"),
        pytest_stderr_str=completed_process.stderr.decode("utf8"),
    )
