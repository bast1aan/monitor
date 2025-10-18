from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Iterator, Iterable, ClassVar, Generic, TypeVar, AsyncIterable, AsyncIterator

from bast1aan.monitor._util import async_iterator, sync_iterator, run_async


class CommandResult(ABC):
    command: Command
    @property
    def error(self) -> bool: ...
    @property
    def __bool__(self) -> bool: ...
    @property
    def __str__(self) -> str: ...


ExtendsCommandResult = TypeVar('ExtendsCommandResult', bound=CommandResult)


@dataclass
class _CommandResult(CommandResult):
    ok: bool
    msg: str
    command: Command

    @property
    def error(self) -> bool:
        return not self.ok

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


class Command(ABC):
    @abstractmethod
    def __call__(self) -> CommandResult: ...
    @abstractmethod
    def __str__(self) -> str: ...


class AsyncCommand(Generic[ExtendsCommandResult], Command):
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
    command: CommandSet
    _results: tuple[CommandResult, ...] = ()

    async def _walk(self) -> AsyncIterator[CommandResult]:
        results = []

        futures = [command.run() for command in self.command.commands if isinstance(command, AsyncCommand)]

        for next_result in asyncio.as_completed(futures):
            result = await next_result
            results.append(result)
            yield result

        for command in self.command.commands:
            if not isinstance(command, AsyncCommand):
                result = command()
                results.append(result)
                yield result

        self._results = tuple(results)

    def __aiter__(self) -> AsyncIterator[CommandResult]:
        return async_iterator(self._results) if self._results else self._walk()

    def __iter__(self) -> Iterator[CommandResult]:
        return iter(self._results) if self._results else sync_iterator(self.__aiter__())

    def __bool__(self) -> bool:
        return all(result for result in iter(self))

    def __str__(self) -> str:
        return '\n'.join((str(result) for result in iter(self)))


class CommandSet(AsyncCommand[CommandSetResult]):
    commands: Tuple[Command, ...]
    def __init__(self, *commands: Command):
        self.commands = commands
    async def run(self) -> CommandSetResult:
        return CommandSetResult(command=self)
    def __str__(self) -> str:
        return '\n'.join((str(command) for command in self.commands))
