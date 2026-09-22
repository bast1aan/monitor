from __future__ import annotations
import socket
from datetime import timedelta, datetime
from enum import Enum

from typing import Iterable, cast

from bast1aan.monitor._util import frozen_dataclass
from bast1aan.monitor.base import ExecutorCommand, CommandResult, CommandSet, ValidationError

class Port(Enum):
    HTTPS = 443
    IMAPS = 993
    SMTPS = 465
    FTPS = 990
    SMTP_STARTTLS = 25
    IMAP_STARTTLS = 143
    @property
    def starttls(self) -> str:
        return {Port.SMTP_STARTTLS: 'smtp', Port.IMAP_STARTTLS: 'imap'}.get(self, '')

OPENSSL_DATETIME_FORMAT = '%b %d %H:%M:%S %Y %Z'

@frozen_dataclass(eq=True)
class _SSLCommand(ExecutorCommand):
    hostname: str
    ipaddress: str
    port: Port
    error: timedelta

    @property
    def command(self) -> str:
        ipaddress = f'[{self.ipaddress}]' if ':' in self.ipaddress else self.ipaddress
        starttls = f'-starttls {self.port.starttls}' if self.port.starttls else ''
        return f"echo QUIT | openssl s_client -showcerts {starttls} -servername {self.hostname} -connect {ipaddress}:{self.port.value} | openssl x509 -noout -dates"

    def _validate(self, msg: str) -> None:
        now = datetime.now()
        for line in msg.split('\n'):
            if line.startswith('notBefore='):
                not_before = datetime.strptime(line[10:], OPENSSL_DATETIME_FORMAT)
                if now < not_before:
                    raise ValidationError(f'Certificate for {self.hostname} on IP address {self.ipaddress} is not yet valid')
            if line.startswith('notAfter='):
                not_after = datetime.strptime(line[9:], OPENSSL_DATETIME_FORMAT)
                if now > not_after - self.error:
                    raise ValidationError(f'Certificate for {self.hostname} on IP address {self.ipaddress} expires on {not_after.isoformat()}')

    def _format_msg(self, stdout: bytes, stderr: bytes) -> str:
        msg = super()._format_msg(stdout, stderr)
        if not stderr:
            return '\n'.join((line for line in msg.split('\n') if line.startswith('notBefore=') or line.startswith('notAfter=')))
        return msg


def ssl_cert_command(hostname: str, port: Port = Port.HTTPS, error: timedelta = timedelta(days=7)) -> CommandSet:
    addrinfo = socket.getaddrinfo(hostname, port.value, proto=socket.IPPROTO_TCP)
    ipaddresses = cast(list[str], [addr[4][0] for addr in addrinfo])

    return CommandSet(*(_SSLCommand(hostname, ipaddress, port, error) for ipaddress in ipaddresses))

