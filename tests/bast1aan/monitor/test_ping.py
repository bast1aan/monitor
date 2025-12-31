import time

from bast1aan.monitor import PingCommand


def test_ping_cmd_waits_for_interval() -> None:
    cmd = PingCommand('127.0.0.1')
    before = time.time()
    cmd()
    cmd()
    cmd()
    cmd()
    after = time.time()
    assert after - before > 0.6

