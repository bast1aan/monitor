import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommandResult:
    ok: bool
    msg: str

    @property
    def error(self) -> bool:
        return not self.ok

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self) -> str:
        return self.msg

    @classmethod
    def Ok(cls, msg: str) -> "CommandResult":
        return cls(True, msg)

    @classmethod
    def Error(cls, msg: str) -> "CommandResult":
        return cls(False, msg)


class Command(ABC):
    @abstractmethod
    def __call__(self) -> CommandResult: ...

class ExecutorCommand(Command):
    command: str
    def __call__(self):
        result = subprocess.run(self.command, shell=True, capture_output=True)
        msg = b'\n'.join((result.stdout or b'', result.stderr or b'')).decode()

        if result.returncode != 0:
            return CommandResult.Error(msg)
        else:
            return CommandResult.Ok(msg)

@dataclass
class PingCommand(ExecutorCommand):
    target: str
    count: int = 1
    @property
    def command(self) -> str:
        return 'ping -c %s %s' % (self.count, self.target)
