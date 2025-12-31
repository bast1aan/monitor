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

def test_ping_cmd_waits_for_interval_even_for_different_objects_with_same_value() -> None:

    cmd1 = PingCommand('127.0.0.1')
    cmd2 = PingCommand('127.0.0.1')
    cmd3 = PingCommand('127.0.0.1')
    cmd4 = PingCommand('127.0.0.1')
    before = time.time()
    cmd1()
    cmd2()
    cmd3()
    cmd4()
    after = time.time()
    assert after - before > 0.6

def test_eq() -> None:
    cmd1 = PingCommand('127.0.0.1')
    cmd2 = PingCommand('127.0.0.1')
    cmd3 = PingCommand('127.0.0.1')
    cmd4 = PingCommand('127.0.0.1')

    assert hash(cmd1) == hash(cmd2) == hash(cmd3) == hash(cmd4)
