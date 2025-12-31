import asyncio
from dataclasses import dataclass
from typing import TypeVar, AsyncIterator, Iterator, Awaitable, Iterable, Callable
from ._typing_extensions import dataclass_transform

T = TypeVar('T')

_loop = None

def sync_iterator(async_iter: AsyncIterator[T]) -> Iterator[T]:
    try:
        while True:
            yield run_async(async_iter.__anext__())
    except StopAsyncIteration:
        pass

async def async_iterator(iter: Iterable[T]) -> AsyncIterator[T]:
    for item in iter:
        yield item

def run_async(coro: Awaitable[T]) -> T:
    global _loop
    if not _loop:
        _loop = asyncio.new_event_loop()
    return _loop.run_until_complete(coro)

@dataclass_transform(frozen_default=True)
def frozen_dataclass(*, eq: bool = False) -> Callable[[type[T]], type[T]]:
    def _frozen_dataclass(cls: type[T]) -> type[T]:
        """ Return dataclass with implemented __hash__ method to satisfy abstract supertypes """
        cls_new = dataclass(frozen=True, eq=eq)(cls)
        cls_new.__abstractmethods__ -= {'__hash__'}  # type: ignore
        if not cls_new.__abstractmethods__:  # type: ignore
            cls_new.__hash__.__isabstractmethod__ = False  # type: ignore
        return cls_new
    return _frozen_dataclass
