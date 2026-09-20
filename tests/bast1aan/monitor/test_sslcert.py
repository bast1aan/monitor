from bast1aan.monitor import sslcert
from bast1aan.monitor.sslcert import Port


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
    assert 'SSL.com' in str(res)

def test_openssl_error_revoked() -> None:
    cmd = sslcert.ssl_cert_command('revoked-ecc-dv.ssl.com')
    res = cmd()
    assert bool(res) is False
    assert 'SSL.com' in str(res)

def test_openssl_starttls() -> None:
    cmd = sslcert.ssl_cert_command('mx1.welmers.net', Port.SMTP_STARTTLS)
    res = cmd()
    assert bool(res) is True, str(res)
