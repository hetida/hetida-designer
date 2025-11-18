import datetime

import pytest

from hetdesrun.dt_utils import (
    resolve_dtexp,
    resolve_interval,
)
from hetdesrun.models.repr_reference import ReproducibilityReference
from hetdesrun.reference_context import (
    get_exec_start_from_reproducibility_context,
    set_reproducibility_reference_context,
)
from hetdesrun.runtime.context import (
    RuntimeExecutionContext,
    TimeInterval,
    set_runtime_exec_context,
)


@pytest.fixture(scope="module")
def fixed_start_timestamp():
    return datetime.datetime(2025, 11, 10, 12, 59, 3, tzinfo=datetime.UTC)


@pytest.fixture
def _set_exec_start_in_context(fixed_start_timestamp):
    set_reproducibility_reference_context(
        ReproducibilityReference(exec_start_timestamp=fixed_start_timestamp)
    )

    yield
    set_reproducibility_reference_context(ReproducibilityReference())


@pytest.mark.usefixtures("_set_exec_start_in_context")
def test_dtexp_parsing_expression_with_context(fixed_start_timestamp):
    rep_ref_exec_start = get_exec_start_from_reproducibility_context()

    assert rep_ref_exec_start == fixed_start_timestamp
    assert resolve_dtexp("now") == fixed_start_timestamp


def test_dtexp_parsing_expression_with_no_context_set(fixed_start_timestamp):
    assert resolve_dtexp("now") != fixed_start_timestamp


@pytest.fixture
def _global_time_interval_in_runtime_context():
    set_runtime_exec_context(
        RuntimeExecutionContext(
            global_time_interval=TimeInterval(
                timestampFrom="2025-09-06T00:00:00+00:00", timestampTo="2025-09-08T00:00:00+00:00"
            )
        )
    )
    yield
    set_runtime_exec_context(RuntimeExecutionContext())


@pytest.mark.usefixtures("_set_exec_start_in_context", "_global_time_interval_in_runtime_context")
def test_resolve_interval(fixed_start_timestamp):
    start, end = resolve_interval("now - 2d", "now")
    assert start == fixed_start_timestamp.replace(day=8)
    assert end == fixed_start_timestamp

    start, end = resolve_interval("2025-08-09T00:00:00+00:00", "2025-08-09T00:00:00+00:00 + 2d")
    assert start == datetime.datetime.fromisoformat("2025-08-09T00:00:00+00:00")
    assert end == datetime.datetime.fromisoformat("2025-08-11T00:00:00+00:00")

    start, end = resolve_interval(None, None)
    assert start == datetime.datetime.fromisoformat("2025-09-06T00:00:00+00:00")
    assert end == datetime.datetime.fromisoformat("2025-09-08T00:00:00+00:00")
