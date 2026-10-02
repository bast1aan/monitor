from typing import Iterator

import re
import pytest
import _pytest.monkeypatch  # todo, import from pytest in newer version instead of _pytest

from bast1aan.monitor import sslcert, CommandSet

@pytest.fixture
def getaddrinfo_v4only(monkeypatch: _pytest.monkeypatch.MonkeyPatch) -> Iterator[None]:
    """" Ugly hack because docker containers where these tests are run don't do IPV6 right by default """
    orig_getaddrinfo = sslcert.socket.getaddrinfo
    def patched_getaddrinfo(*args, **kwargs):
        addrinfo = orig_getaddrinfo(*args, **kwargs)
        return [addr for addr in addrinfo if ':' not in addr[4][0]]

    monkeypatch.setattr(sslcert.socket, 'getaddrinfo', patched_getaddrinfo)
    yield None
    monkeypatch.undo()

def test_github() -> None:
    cmd = sslcert.ssl_cert_command('github.com')
    res = cmd()
    assert bool(res) is True

def test_openssl_error_no_cert_error() -> None:
    cmd = sslcert.ssl_cert_command('localhost')
    res = cmd()
    assert bool(res) is False
    assert 'unable to load certificate' in str(res)

def test_openssl_error_expired() -> None:
    cmd = sslcert.ssl_cert_command('expired-ecc-dv.ssl.com')
    res = cmd()
    assert bool(res) is False
    assert re.search(r'Certificate for expired-ecc-dv.ssl.com on IP address (.+?) expires on 20(.+)', str(res))

def test_openssl_error_expired_in_commandset() -> None:
    cmd = CommandSet(sslcert.ssl_cert_command('expired-ecc-dv.ssl.com'),)
    res = cmd()
    assert bool(res) is False
    assert re.search(r'Certificate for expired-ecc-dv.ssl.com on IP address (.+?) expires on 20(.+)', str(res))

def test_walking_over_commandset_gives_correct_error() -> None:
    cmd = CommandSet(sslcert.ssl_cert_command('expired-ecc-dv.ssl.com'),)
    results = [res for res in cmd()]
    assert bool(results[0]) is False
    assert re.search(r'Certificate for expired-ecc-dv.ssl.com on IP address (.+?) expires on 20(.+)', str(results[0]))

def test_openssl_error_revoked() -> None:
    cmd = sslcert.ssl_cert_command('revoked-ecc-dv.ssl.com')
    res = cmd()
    assert bool(res) is False
    assert 'SSL.com' in str(res)

def test_openssl_starttls(getaddrinfo_v4only: None) -> None:
    cmd = sslcert.ssl_cert_command('mx1.welmers.net', sslcert.Port.SMTP_STARTTLS)
    res = cmd()
    assert bool(res) is True, str(res)

def test_broken(getaddrinfo_v4only: None) -> None:
    cmd = sslcert.ssl_cert_command('devproxy.welmers.net')
    res = cmd()
    assert bool(res) is False, str(res)
    assert re.search(r'Certificate for devproxy.welmers.net on IP address (.+?) expires on 20(.+)', str(res))
