from bast1aan.monitor.base import PingCommand, IPV4, IPV6


def test_ping_success():
    ping_command = PingCommand('localhost')
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (::1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg

def test_ping_failure():
    ping_command = PingCommand('fliepsflops')
    result = ping_command()
    assert bool(result) is False
    msg = str(result)
    assert 'fliepsflops: Name or service not known' in msg


def test_ping_ipv4_success():
    ping_command = PingCommand('localhost', only=IPV4)
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (127.0.0.1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg

def test_ping_ipv6_success():
    ping_command = PingCommand('localhost', only=IPV6)
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (::1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg
