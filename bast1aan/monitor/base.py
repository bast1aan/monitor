from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Iterator, Iterable, ClassVar, Generic, TypeVar, AsyncIterable, AsyncIterator, Hashable, \
    Optional, Callable

from bast1aan.monitor._util import async_iterator, sync_iterator, run_async, frozen_dataclass

ALL_SUCCEED = all
ANY_SUCCEEDS = any


class CommandResult(ABC):
    command: Command
    @abstractmethod
    def __bool__(self) -> bool: ...
    @abstractmethod
    def __str__(self) -> str: ...
    @property
    def error(self) -> bool:
        return not bool(self)


ExtendsCommandResult = TypeVar('ExtendsCommandResult', bound=CommandResult)


@dataclass
class _CommandResult(CommandResult):
    ok: bool
    msg: str
    command: Command

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self) -> str:
        return self.msg

    @classmethod
    def Ok(cls, msg: str, command: Command) -> CommandResult:
        return cls(True, msg, command)

    @classmethod
    def Error(cls, msg: str, command: Command) -> CommandResult:
        return cls(False, msg, command)


class Command(Hashable, ABC):
    @abstractmethod
    def __call__(self) -> CommandResult: ...
    @abstractmethod
    def __str__(self) -> str: ...

class AsyncCommand(Command, Generic[ExtendsCommandResult]):
    _in_call: ClassVar[bool] = False

    @abstractmethod
    async def run(self) -> ExtendsCommandResult: ...

    def __call__(self) -> ExtendsCommandResult:
        if self._in_call:
            raise RuntimeError('AsyncCommand may not be called recursively in a synchronous manner')
        try:
            AsyncCommand._in_call = True
            return run_async(self.run())
        finally:
            AsyncCommand._in_call = False


class ExecutorCommand(AsyncCommand):
    @property
    @abstractmethod
    def command(self) -> str: ...

    async def run(self) -> CommandResult:
        process = await asyncio.subprocess.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        msg = b'\n'.join((stdout, stderr)).decode()

        if process.returncode != 0:
            return _CommandResult.Error(msg, self)
        else:
            return _CommandResult.Ok(msg, self)

    def __str__(self) -> str:
        return self.command


@dataclass
class CommandSetResult(CommandResult, AsyncIterable[CommandResult], Iterable[CommandResult]):
    command: Command
    iterator: AsyncIterator[CommandResult]
    succeeds_if: Callable[[Iterable], bool]
    _results: tuple[CommandResult, ...] = ()

    async def _walk(self) -> AsyncIterator[CommandResult]:
        results = []
        async for result in self.iterator:
            results.append(result)
            yield result
        self._results = tuple(results)

    def __aiter__(self) -> AsyncIterator[CommandResult]:
        return async_iterator(self._results) if self._results else self._walk()

    def __iter__(self) -> Iterator[CommandResult]:
        return iter(self._results) if self._results else sync_iterator(self.__aiter__())

    def __bool__(self) -> bool:
        return self.succeeds_if(self)

    def __str__(self) -> str:
        return '\n'.join((str(result) for result in iter(self)))


class CommandSet(AsyncCommand[CommandSetResult]):
    commands: Tuple[Command, ...]
    _succeeds_if: Callable[[Iterable], bool]
    def __init__(self, *commands: Command, succeeds_if: Callable[[Iterable], bool] = ALL_SUCCEED):
        self.commands = commands
        self._succeeds_if = succeeds_if
    async def run(self) -> CommandSetResult:
        return CommandSetResult(command=self, iterator=self._walk(), succeeds_if=self._succeeds_if)
    def __str__(self) -> str:
        return '\n'.join((str(command) for command in self.commands))
    def __hash__(self) -> int:
        return hash(self.commands)
    async def _walk(self) -> AsyncIterator[CommandResult]:
        futures = [command.run() for command in self.commands if isinstance(command, AsyncCommand)]

        for next_result in asyncio.as_completed(futures):
            async for subresult in _walk_over_result(await next_result):
                yield subresult

        for command in self.commands:
            if not isinstance(command, AsyncCommand):
                yield command()


@frozen_dataclass()
class DependingCommandSet(AsyncCommand[CommandSetResult]):
    first_command: AsyncCommand
    if_succeeds: Optional[AsyncCommand] = None
    if_fails: Optional[AsyncCommand] = None
    succeeds_if: Callable[[Iterable], bool] = ALL_SUCCEED

    async def run(self) -> CommandSetResult:
        return CommandSetResult(command=self, iterator=self._walk(), succeeds_if=self.succeeds_if)

    async def _walk(self) -> AsyncIterator[CommandResult]:
        async for subresult in _walk_over_result(first_result := await self.first_command.run()):
            yield subresult
        if first_result and self.if_succeeds is not None:
            async for subresult in _walk_over_result(await self.if_succeeds.run()):
                yield subresult
        if not first_result and self.if_fails is not None:
            async for subresult in _walk_over_result(await self.if_fails.run()):
                yield subresult

    def __str__(self) -> str:
        return str(self.first_command)


def try_until_succeeds(*commands: AsyncCommand, count: int = 1) -> DependingCommandSet:
    commands = commands * count
    return DependingCommandSet(
        commands[0],
        if_fails=try_until_succeeds(*commands[1:]) if len(commands) > 2 else commands[1],
        succeeds_if=ANY_SUCCEEDS
    )


async def _walk_over_result(result: CommandResult) -> AsyncIterator[CommandResult]:
    if isinstance(result, CommandSetResult):
        async for subresult in result:
            yield subresult
    else:
        yield result
