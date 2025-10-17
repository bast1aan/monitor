from __future__ import annotations
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Iterator, Iterable


class CommandResult(ABC):
    command: Command
    @property
    def error(self) -> bool: ...
    @property
    def __bool__(self) -> bool: ...
    @property
    def __str__(self) -> str: ...


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


class ExecutorCommand(Command):
    @property
    @abstractmethod
    def command(self) -> str: ...

    def __call__(self) -> CommandResult:
        result = subprocess.run(self.command, shell=True, capture_output=True)
        msg = b'\n'.join((result.stdout or b'', result.stderr or b'')).decode()

        if result.returncode != 0:
            return _CommandResult.Error(msg, self)
        else:
            return _CommandResult.Ok(msg, self)

    def __str__(self) -> str:
        return self.command


@dataclass
class CommandSetResult(CommandResult, Iterable[CommandResult]):
    command: CommandSet
    _results: tuple[CommandResult, ...] = ()

    def _walk(self) -> Iterator[CommandResult]:
        results = []
        for command in self.command.commands:
            result = command()
            results.append(result)
            yield result
        self._results = tuple(results)

    def __iter__(self) -> Iterator[CommandResult]:
        return iter(self._results) if self._results else self._walk()

    def __bool__(self) -> bool:
        return all(result for result in iter(self))

    def __str__(self) -> str:
        return '\n'.join((str(result) for result in iter(self)))


class CommandSet(Command):
    commands: Tuple[Command, ...]
    def __init__(self, *commands: Command):
        self.commands = commands
    def __call__(self) -> CommandSetResult:
        return CommandSetResult(command=self)
    def __str__(self) -> str:
        return '\n'.join((str(command) for command in self.commands))
