from bast1aan.monitor.sslcert import ssl_cert_command

def test_github() -> None:
    cmd = ssl_cert_command('github.com')
    res = cmd()
    assert bool(res) is True
