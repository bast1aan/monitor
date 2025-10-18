import asyncio
from typing import TypeVar, AsyncIterator, Iterator, Awaitable

T = TypeVar('T')

_loop = None

def sync_iterator(async_iter: AsyncIterator[T]) -> Iterator[T]:
    try:
        while True:
            yield run_async(async_iter.__anext__())
    except StopAsyncIteration:
        pass

def run_async(coro: Awaitable[T]) -> T:
    global _loop
    if not _loop:
        _loop = asyncio.new_event_loop()
    return _loop.run_until_complete(coro)
