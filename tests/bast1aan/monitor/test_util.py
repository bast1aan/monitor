import asyncio
from typing import AsyncIterator

from bast1aan.monitor import _util

def test_util() -> None:
    async def async_iterator() -> AsyncIterator[str]:
        await asyncio.sleep(0.01)
        yield 'bla'
        await asyncio.sleep(0.03)
        yield 'bloep'

    result = [i for i in _util.sync_iterator(async_iterator())]
    assert result == ['bla', 'bloep']
