from __future__ import annotations
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Tuple, Iterator


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

IPV4: Literal[4] = 4
IPV6: Literal[6] = 6

@dataclass
class PingCommand(ExecutorCommand):
    target: str
    count: int = 1
    only: Literal[0, 4, 6] = 0
    @property
    def command(self) -> str:
        args = ['-c', str(self.count)]
        if self.only == IPV4:
            args.append('-4')
        if self.only == IPV6:
            args.append('-6')
        return 'ping %s %s' % (' '.join(args), self.target)
