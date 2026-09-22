import re

from bast1aan.monitor import sslcert, CommandSet


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

def test_openssl_starttls() -> None:
    cmd = sslcert.ssl_cert_command('mx1.welmers.net', sslcert.Port.SMTP_STARTTLS)
    res = cmd()
    assert bool(res) is True, str(res)

def test_broken() -> None:
    cmd = sslcert.ssl_cert_command('devproxy.welmers.net')
    res = cmd()
    assert bool(res) is True, str(res)
