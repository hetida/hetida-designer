import pytest

from hetdesrun.utils import cache_conditionally


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

    _ = await squaring(12)

    assert squaring.cache_ == {12: 144}

    _ = await squaring(6)

    assert squaring.cache_ == {12: 144}
