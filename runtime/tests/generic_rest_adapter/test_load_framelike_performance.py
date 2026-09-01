"""Performance guards for the framelike load parse chain (time and peak memory).

The generic REST framelike load path was switched from ``pd.read_json`` (reading the whole
response into memory) to a streaming ``pyarrow`` JSON reader followed by ``Table.to_pandas``. These
tests guard that win against regressions: they compare the two "``resp.raw`` -> ``DataFrame``" parse
pipelines on identical in-memory bytes and assert the new one is both meaningfully faster and uses
meaningfully less peak memory.

The **new** pipeline under test is the *actual production code*: ``_parse_new`` calls
``load_framelike.parse_framelike_response_stream`` - the same helper ``load_framelike_data`` uses -
so this is not a reimplementation. The **old** pipeline (``pd.read_json``) no longer exists in the
code base and is reproduced here purely as the reference baseline to compare against.

Making the measurements stable on resource-restricted / few-core CI runners:

* **No network / no HTTP client.** The request is excluded on purpose - it adds scheduling and
  socket noise (flakiness) and is not where the difference comes from; the parsing is. Both
  pipelines read the exact same bytes from an ``io.BytesIO``.
* **ratios, not absolute numbers.** Both pipelines are CPU-bound, so machine speed and load scale
  them together and cancel out. The new pipeline uses pyarrow with threads (production config), so
  on fewer cores the ratio only rises toward its single-threaded worst case (~0.59) - still well
  under the asserted 0.75. The memory ratio is even unit-independent, so it is portable.

Time: minimum wall-clock over several repetitions (least-contended run; far more stable than a mean
under CI jitter). Locally ~0.4 (threaded) to ~0.59 (single core); asserted < 0.75.

Memory: a pyarrow/pandas DataFrame lives largely in C buffers that ``tracemalloc`` cannot see, so we
use the OS resident-set size. Each chain runs in its **own fresh subprocess** where, after importing
the modules and building the input, we **reset the peak-RSS counter** (write ``5`` to
``/proc/self/clear_refs``, Linux >= 4.0) and then read the peak RSS (``VmHWM`` from
``/proc/self/status``) again after parsing - the delta is the parse's own peak footprint. Resetting
is essential: (a) a subprocess *inherits its parent's* peak-RSS high-water mark through ``exec`` (so
a big pytest parent would otherwise swamp the measurement), and (b) the import peak (importing the
production helper pulls in the hetdesrun stack) would otherwise mask the parse. The subprocess also
pins pyarrow to one thread (see ``__main__``) so the peak is deterministic. Linux-only; the memory
test skips elsewhere. Locally ~0.1; asserted < 0.75.
"""

import gc
import io
import os
import subprocess
import sys
import time
from collections.abc import Callable

import pandas as pd
import pyarrow as pa
import pytest

from hetdesrun.adapters.generic_rest.load_framelike import parse_framelike_response_stream

# A size large enough that the measurement dominates fixed overhead, yet small enough to stay fast
# and memory-light on constrained CI (the old chain peaks at only ~40 MiB above baseline here).
_NUM_ROWS = 50_000
_REPETITIONS = 7
_MEM_MEASURE_RUNS = 3
# The new chain must take / allocate less than this fraction of the old chain.
_MAX_TIME_RATIO = 0.75
_MAX_MEM_RATIO = 0.75


def _make_timeseries_ndjson(num_rows: int) -> bytes:
    """Newline-delimited JSON as a generic REST timeseries endpoint would stream it."""
    lines = [
        b'{"timeseriesId":"sensor_%d","timestamp":"2020-01-01T%02d:%02d:%02d.000Z","value":%d.%03d}'
        % (i % 50, (i // 3600) % 24, (i // 60) % 60, i % 60, i % 1000, i % 1000)
        for i in range(num_rows)
    ]
    return b"\n".join(lines) + b"\n"


def _parse_old(raw: bytes) -> pd.DataFrame:
    """Reference baseline (removed from production): stream into pandas' JSON reader."""
    return pd.read_json(io.BytesIO(raw), lines=True)


def _parse_new(raw: bytes) -> pd.DataFrame:
    """The production parse core, as load_framelike_data invokes it (timeseries endpoint)."""
    return parse_framelike_response_stream(io.BytesIO(raw), "timeseries")


def _best_time(parse: Callable[[bytes], pd.DataFrame], raw: bytes) -> float:
    """Minimum wall-clock duration of ``parse(raw)`` over the configured repetitions."""
    best = float("inf")
    for _ in range(_REPETITIONS):
        start = time.perf_counter()
        parse(raw)
        best = min(best, time.perf_counter() - start)
    return best


def _peak_rss_kib() -> int:
    """Current peak resident set size (``VmHWM``) of this process, in KiB (Linux only)."""
    with open("/proc/self/status") as status:
        for line in status:
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    raise RuntimeError("VmHWM not present in /proc/self/status")


def _reset_peak_rss() -> None:
    """Reset this process' peak-RSS high-water mark to its current RSS (Linux >= 4.0)."""
    with open("/proc/self/clear_refs", "w") as clear_refs:
        clear_refs.write("5")


def _measure_parse_peak_rss(parse: Callable[[bytes], pd.DataFrame], raw: bytes) -> float:
    """Peak RSS (KiB) added by parsing ``raw``.

    A warm-up parse triggers one-time lazy allocations first; then the peak-RSS counter is reset (so
    the inherited-parent and import peaks are excluded, see module docstring) and the parse's own
    footprint is measured. Linux-only; called from the ``__main__`` entry below, one fresh process
    per chain.
    """
    parse(raw)  # warm-up: pay one-time lazy allocations (e.g. pyarrow init) before measuring
    gc.collect()
    _reset_peak_rss()
    base = _peak_rss_kib()
    for _ in range(_MEM_MEASURE_RUNS):
        result = parse(raw)
        del result
    return float(_peak_rss_kib() - base)


def _peak_rss_in_fresh_subprocess(kind: str) -> float:
    """Run one chain in a fresh interpreter (own clean peak-RSS mark) and return its peak-RSS delta.

    The child re-runs this file's ``__main__``; it imports the production helper (hence hetdesrun),
    so it needs the runtime root on its path. Coverage's subprocess hooks are stripped too: under
    pytest-cov the child would otherwise trace this helper, adding memory and time noise.
    """
    runtime_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = {k: v for k, v in os.environ.items() if not k.startswith(("COV_CORE", "COVERAGE"))}
    env["PYTHONPATH"] = os.pathsep.join([runtime_root, env.get("PYTHONPATH", "")]).rstrip(
        os.pathsep
    )
    completed = subprocess.run(
        [sys.executable, __file__, kind, str(_NUM_ROWS)],
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
        env=env,
    )
    for line in completed.stdout.splitlines():
        if line.startswith("PEAK_RSS="):
            return float(line[len("PEAK_RSS=") :])
    raise AssertionError(
        "subprocess did not report PEAK_RSS.\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )


@pytest.mark.performance
def test_new_framelike_parse_chain_is_faster_than_old() -> None:
    raw = _make_timeseries_ndjson(_NUM_ROWS)

    # Both chains must produce equivalent output (this also warms up imports/allocator).
    df_old = _parse_old(raw)
    df_new = _parse_new(raw)
    assert df_old.shape == df_new.shape == (_NUM_ROWS, 3)
    assert isinstance(df_new["timestamp"].dtype, pd.DatetimeTZDtype)

    # One more warm-up each so the first measured repetition is not penalized.
    _parse_old(raw)
    _parse_new(raw)

    old_best = _best_time(_parse_old, raw)
    new_best = _best_time(_parse_new, raw)

    assert old_best > 0.0  # guard against a degenerate (unmeasurably small) baseline
    ratio = new_best / old_best
    assert new_best < _MAX_TIME_RATIO * old_best, (
        "New framelike parse chain is not sufficiently faster than the old pd.read_json baseline: "
        f"new={new_best * 1000:.1f}ms old={old_best * 1000:.1f}ms "
        f"ratio={ratio:.3f} (must be < {_MAX_TIME_RATIO})"
    )


@pytest.mark.performance
def test_new_framelike_parse_chain_uses_less_peak_memory_than_old() -> None:
    if not os.path.exists("/proc/self/clear_refs"):
        pytest.skip("peak-RSS measurement relies on Linux /proc (clear_refs / VmHWM)")

    # Each chain runs in its own fresh subprocess where the peak-RSS counter is reset after imports,
    # so the reported delta isolates the parse's peak footprint (see module docstring).
    old_peak = _peak_rss_in_fresh_subprocess("old")
    new_peak = _peak_rss_in_fresh_subprocess("new")

    assert old_peak > 0.0  # guard against a degenerate baseline
    ratio = new_peak / old_peak
    assert new_peak < _MAX_MEM_RATIO * old_peak, (
        "New framelike parse chain does not use sufficiently less peak memory than the old "
        f"pd.read_json baseline: new={new_peak / 1024:.1f}MiB old={old_peak / 1024:.1f}MiB "
        f"ratio={ratio:.3f} (must be < {_MAX_MEM_RATIO})"
    )


if __name__ == "__main__":
    # Entry point used by test_..._peak_memory: measure one chain's peak-RSS delta in this fresh
    # process and print it for the parent to read. Usage: <this file> <old|new> <num_rows>
    #
    # Pin pyarrow to a single thread: production's parse uses use_threads=True, but threaded
    # to_pandas allocates per-thread buffers whose peak is nondeterministic (and core-count
    # dependent). One thread makes the peak-memory measurement stable and is the conservative worst
    # case; the production helper is still called unchanged.
    pa.set_cpu_count(1)
    _kind = sys.argv[1]
    _rows = int(sys.argv[2])
    _raw = _make_timeseries_ndjson(_rows)
    _parse = _parse_old if _kind == "old" else _parse_new
    print(f"PEAK_RSS={_measure_parse_peak_rss(_parse, _raw)}")
