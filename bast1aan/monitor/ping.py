from __future__ import annotations
import asyncio
import time
from collections import defaultdict

from typing import Literal

from bast1aan.monitor._util import frozen_dataclass
from bast1aan.monitor.base import ExecutorCommand, CommandResult

IPV4: Literal[4] = 4
IPV6: Literal[6] = 6
_previous_runs: dict[PingCommand, float] = defaultdict(float)


@frozen_dataclass(eq=True)
class PingCommand(ExecutorCommand):
    target: str
    count: int = 1
    only: Literal[0, 4, 6] = 0
    interval: float = 0.2
    @property
    def command(self) -> str:
        args = ['-c', str(self.count)]
        if self.only == IPV4:
            args.append('-4')
        if self.only == IPV6:
            args.append('-6')
        return 'ping %s %s' % (' '.join(args), self.target)

    async def run(self) -> CommandResult:
        await self._wait_if_necessary()
        return await super().run()

    async def _wait_if_necessary(self) -> None:
        wait = (_previous_runs[self] + self.interval) - time.time()
        if wait > 0.0:
            await asyncio.sleep(wait)
        _previous_runs[self] = time.time()

