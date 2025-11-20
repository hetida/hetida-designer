import timeit

import pytest

from hetdesrun.component.load import hash_code


def benchmark_base_function():
    sum(range(100000))


@pytest.fixture(scope="session")
def benchmark_base():
    return timeit.timeit(benchmark_base_function, number=100) / 100


def test_hash_code_fast_enough(benchmark_base):
    """Test that code hashing is fast

    Code hashing occurs at each execution, for each component, to guarantee
    that the imported and executed code module is exactly the desired one
    and not some previous version, in particular for draft components.

    Therefore it must be fast.

    Come components may include longer test / release wirings in their
    code.

    """
    long_code = "a" * 1_000_000

    how_often = 500
    hash_code_time = timeit.timeit(lambda: hash_code(long_code), number=how_often)
    mean_time = hash_code_time / how_often

    assert mean_time < benchmark_base
