from __future__ import annotations
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Iterator


@dataclass
class CommandResult:
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
    def Ok(cls, msg: str, command: Command) -> "CommandResult":
        return cls(True, msg, command)

    @classmethod
    def Error(cls, msg: str, command: Command) -> "CommandResult":
        return cls(False, msg, command)


class Command(ABC):
    @abstractmethod
    def __call__(self) -> CommandResult: ...
    @abstractmethod
    def __str__(self) -> str: ...


class ExecutorCommand(Command):
    command: str
    def __call__(self) -> CommandResult:
        result = subprocess.run(self.command, shell=True, capture_output=True)
        msg = b'\n'.join((result.stdout or b'', result.stderr or b'')).decode()

        if result.returncode != 0:
            return CommandResult.Error(msg, self)
        else:
            return CommandResult.Ok(msg, self)

    def __str__(self) -> str:
        return self.command


class CommandSet:
    commands: Tuple[Command, ...]
    def __init__(self, *commands: Command):
        self.commands = commands
    def __call__(self) -> Iterator[CommandResult]:
        for command in self.commands:
            yield command()

