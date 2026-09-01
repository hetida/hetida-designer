"""Performance guard for the raw runtime-result serialization vs the old model_dump path.

The runtime result serialization was switched from ``json.loads(df.to_json())`` - parsing pandas'
own JSON output back into Python objects only to have msgspec re-encode it - to splicing the bytes
pandas already produced straight into the response via ``msgspec.Raw``. That drops a full parse
pass *and* the re-encode of the payload. This test guards the win against regressions: it compares
the two "``DataFrame`` -> JSON bytes" pipelines on an identical in-memory frame and asserts the raw
one is meaningfully faster.

Following ``test_load_framelike_performance.py``:

* **Self-contained.** The two pipelines are reproduced with only pandas + msgspec (no hetdesrun
  import), so the subprocess stays lean and the measurement is not swamped by import cost.
* **Ratios, not absolute numbers.** Both pipelines are CPU-bound on the same core, so machine speed
  scales them together and cancels out.
* **Minimum wall-clock** over several repetitions (least-contended run; far more stable than a mean
  under CI jitter).

Locally the raw pipeline runs at ~0.2x the old one (~4-5x faster); asserted < 0.6 to leave generous
headroom for constrained CI.
"""

import json
import time
from collections.abc import Callable

import msgspec
import numpy as np
import pandas as pd
import pytest

_NUM_ROWS = 50_000
_NUM_COLS = 5
_REPETITIONS = 7
# The raw pipeline must take less than this fraction of the old one.
_MAX_TIME_RATIO = 0.6


def _make_frame(num_rows: int, num_cols: int) -> pd.DataFrame:
    """A numeric frame with some NaNs, so the null-handling path pandas' ``to_json`` takes (the
    reason the old code round-tripped through ``json.loads`` at all) is exercised."""
    data = {f"c{i}": (np.arange(num_rows, dtype=float) + i) for i in range(num_cols)}
    for column in data.values():
        column[::100] = np.nan
    return pd.DataFrame(data)


def _dump_old(df: pd.DataFrame) -> bytes:
    """Old chain: parse pandas' JSON back to Python, then let msgspec re-encode it."""
    return msgspec.json.encode({"__data__": json.loads(df.to_json(date_format="iso"))})


def _dump_raw(df: pd.DataFrame) -> bytes:
    """New chain: splice pandas' JSON bytes verbatim via ``msgspec.Raw``."""
    return msgspec.json.encode({"__data__": msgspec.Raw(df.to_json(date_format="iso").encode())})


def _best_time(dump: Callable[[pd.DataFrame], bytes], df: pd.DataFrame) -> float:
    best = float("inf")
    for _ in range(_REPETITIONS):
        start = time.perf_counter()
        dump(df)
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.performance
def test_raw_result_serialization_is_faster_than_dump() -> None:
    df = _make_frame(_NUM_ROWS, _NUM_COLS)

    # Both pipelines must produce equivalent JSON (this also warms up imports/allocator).
    assert msgspec.json.decode(_dump_old(df)) == msgspec.json.decode(_dump_raw(df))

    # One more warm-up each so the first measured repetition is not penalized.
    _dump_old(df)
    _dump_raw(df)

    old_best = _best_time(_dump_old, df)
    raw_best = _best_time(_dump_raw, df)

    assert old_best > 0.0  # guard against a degenerate (unmeasurably small) baseline
    ratio = raw_best / old_best
    assert raw_best < _MAX_TIME_RATIO * old_best, (
        "New raw (msgspec.Raw) result serialization is not sufficiently faster than the old "
        f"json.loads(df.to_json()) dump chain: raw={raw_best * 1000:.1f}ms "
        f"old={old_best * 1000:.1f}ms ratio={ratio:.3f} (must be < {_MAX_TIME_RATIO})"
    )
