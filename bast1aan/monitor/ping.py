from dataclasses import dataclass
from typing import Literal

from bast1aan.monitor.base import ExecutorCommand

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
