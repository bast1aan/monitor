from __future__ import annotations
import socket
from datetime import timedelta, datetime
from enum import Enum

from typing import Iterable, cast

from bast1aan.monitor._util import frozen_dataclass
from bast1aan.monitor.base import ExecutorCommand, CommandResult, CommandSet

class Port(Enum):
    HTTPS = 443
    IMAPS = 993
    SMTPS = 465
    FTPS = 990

OPENSSL_DATETIME_FORMAT = '%b %d %H:%M:%S %Y %Z'

@frozen_dataclass(eq=True)
class _SSLCommand(ExecutorCommand):
    hostname: str
    ipaddress: str
    port: Port

    @property
    def command(self) -> str:
        ipaddress = self.ipaddress
        if ':' in ipaddress:
            ipaddress = f'[{ipaddress}]'
        return f"echo QUIT | openssl s_client -showcerts -servername {self.hostname} -connect {ipaddress}:{self.port.value} | openssl x509 -noout -dates"

    def _format_msg(self, stdout: bytes, stderr: bytes) -> str:
        msg = super()._format_msg(stdout, stderr)
        if not stderr:
            return '\n'.join((line for line in msg.split('\n') if line.startswith('notBefore=') or line.startswith('notAfter=')))
        return msg


def ssl_cert_command(hostname: str, port: Port = Port.HTTPS, error: timedelta = timedelta(days=7)) -> CommandSet:
    def output_contains_valid_dates(command_results: Iterable[CommandResult]) -> bool:
        results = tuple(command_results)  # force the iterator to be completely consumed
        now = datetime.now()
        for res in results:
            if not bool(res):
                return False
            output = str(res)
            for line in output.split('\n'):
                if line.startswith('notBefore='):
                    not_before = datetime.strptime(line[10:], OPENSSL_DATETIME_FORMAT)
                    if now < not_before:
                        return False
                if line.startswith('notAfter='):
                    not_after = datetime.strptime(line[9:], OPENSSL_DATETIME_FORMAT)
                    if now > not_after - error:
                        return False
        return True

    addrinfo = socket.getaddrinfo(hostname, port.value, proto=socket.IPPROTO_TCP)
    ipaddresses = cast(list[str], [addr[4][0] for addr in addrinfo])

    return CommandSet(*(_SSLCommand(hostname, ipaddress, port) for ipaddress in ipaddresses), succeeds_if=output_contains_valid_dates)

