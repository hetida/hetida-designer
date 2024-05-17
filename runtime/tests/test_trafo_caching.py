import asyncio
import os

import pytest

from hetdesrun.trafoutils.io.load import (
    transformation_revision_from_python_code,
)
from hetdesrun.utils import State, cache_conditionally


def test_basic_caching() -> None:
    @cache_conditionally(lambda num: num > 42)
    def squaring(base_num):
        return base_num**2

    assert squaring.cache_ is not None
    assert squaring.cache_ == {}

    _ = squaring(10)

    assert squaring.cache_ == {10: 100}

    _ = squaring(4)

    assert squaring.cache_ == {10: 100}


@pytest.mark.asyncio
async def test_basic_caching_with_async_func() -> None:
    async def calculation(num):
        return num**2

    @cache_conditionally(lambda num: num > 42)
    async def squaring(base_num):
        square = await calculation(base_num)
        return square

    assert squaring.cache_ is not None
    assert squaring.cache_ == {}

    assert squaring.lock_ is not None
    assert squaring.lock_.locked() is False

    _ = await squaring(12)

    assert squaring.cache_ == {12: 144}

    _ = await squaring(6)

    assert squaring.cache_ == {12: 144}


@pytest.mark.asyncio
async def test_async_lock_for_cache() -> None:
    """This function provokes a scenario in which two async functions try to access the cache at the
    same time:
    * Task 1 waits until task 2 has started (signaled by order_event)
    * While task 2 awaits completion, task 1 tries to access the cache, but should need to wait
    * Task 2 finds an empty cache, sets a computation event and fills the cache
    * Should task 1 perform a calculation because it accessed the cache before task 2 filled it,
      the computation event is cleared, signaling that 2 computation events happened,
      which would be faulty behavior
    """
    order_event = asyncio.Event()  # Used to create the conflict
    computation_event = asyncio.Event()  # Used to track whether a computation occurs

    async def calculation(num):
        await asyncio.sleep(0.1)  # Simulate time intensive computation
        return num**2

    @cache_conditionally(lambda num: num > 42)
    async def squaring(base_num):
        square = await calculation(base_num)
        if not computation_event.is_set():  # Task 2 should set this
            computation_event.set()
        else:  # Task 1 should never reach this, if it does the event is cleared
            computation_event.clear()
        return square

    async def run_squaring(num):
        await order_event.wait()  # Wait until task 2 starts
        _ = await squaring(num)

    async def run_second_squaring(num):
        order_event.set()  # Allow task 1 to start
        _ = await squaring(num)

    # Simulate two async tasks trying to reach the cache simultaneously
    task1 = asyncio.create_task(run_squaring(23))
    task2 = asyncio.create_task(run_second_squaring(23))

    await asyncio.gather(task1, task2)

    assert computation_event.is_set() is True


def test_trafo_caching() -> None:

    # Load test trafos
    def load_trafo1():
        path = os.path.join(
            "data",
            "components",
            "alerts-from-score_100_38f168ef-cb06-d89c-79b3-0cd823f32e9d.py",
        )
        with open(path) as f:
            code = f.read()

        trafo = transformation_revision_from_python_code(code)

        return trafo

    def load_trafo2():
        path = os.path.join(
            "data",
            "components",
            "test_optional_inputs_component.py",
        )
        with open(path) as f:
            code = f.read()

        trafo = transformation_revision_from_python_code(code)

        return trafo

    @cache_conditionally(lambda trafo: trafo.state != State.DRAFT)
    def load_trafo_with_caching(trafo_num):
        return load_trafo1() if trafo_num < 42 else load_trafo2()

    _ = load_trafo_with_caching(23)  # Is released, should be cached
    assert load_trafo_with_caching.cache_ == {23: load_trafo1()}

    _ = load_trafo_with_caching(69)  # Is draft, should not be cached
    assert load_trafo_with_caching.cache_ == {23: load_trafo1()}
