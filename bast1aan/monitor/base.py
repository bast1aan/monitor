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

        msg = self._format_msg(stdout, stderr)

        if process.returncode != 0:
            return _CommandResult.Error(msg, self)
        else:
            try:
                self._validate(msg)
                return _CommandResult.Ok(msg, self)
            except ValidationError as e:
                return _CommandResult.Error(e.msg, self)

    def _validate(self, msg: str) -> None:
        """ :raises: ValidationError """

    def _format_msg(self, stdout: bytes, stderr: bytes) -> str:
        return b'\n'.join((stdout, stderr)).decode()

    def __str__(self) -> str:
        return self.command


@dataclass
class CommandSetResult(CommandResult, AsyncIterable[CommandResult], Iterable[CommandResult]):
    command: Command
    iterator: AsyncIterator[CommandResult]
    succeeds_if: Callable[[Iterable], bool]
    _results: tuple[CommandResult, ...] = ()
    _first_level_results: tuple[CommandResult, ...] = ()

    async def _walk(self) -> AsyncIterator[CommandResult]:
        results: list[CommandResult] = []
        first_level_results: list[CommandResult] = []
        async for result in self.iterator:
            first_level_results.append(result)
            if isinstance(result, CommandSetResult):
                async for subresult in result:
                    results.append(subresult)
                    yield subresult
            else:
                results.append(result)
                yield result

        self._results = tuple(results)
        self._first_level_results = tuple(first_level_results)

    def __aiter__(self) -> AsyncIterator[CommandResult]:
        return async_iterator(self._results) if self._results else self._walk()

    def __iter__(self) -> Iterator[CommandResult]:
        return iter(self._results) if self._results else sync_iterator(self.__aiter__())

    def __bool__(self) -> bool:
        if not self._first_level_results:
            list(self) # consume the iterator to force results
        return self.succeeds_if(self._first_level_results)

    def __str__(self) -> str:
        return '\n'.join((str(result) for result in self))


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
            yield await next_result

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
        yield (first_result := await self.first_command.run())

        if first_result and self.if_succeeds is not None:
            yield await self.if_succeeds.run()

        if not first_result and self.if_fails is not None:
            yield await self.if_fails.run()

    def __str__(self) -> str:
        return str(self.first_command)


def try_until_succeeds(*commands: AsyncCommand, count: int = 1) -> DependingCommandSet:
    commands = commands * count
    return DependingCommandSet(
        commands[0],
        if_fails=try_until_succeeds(*commands[1:]) if len(commands) > 2 else commands[1],
        succeeds_if=ANY_SUCCEEDS
    )


@dataclass
class ValidationError(Exception):
    msg: str
