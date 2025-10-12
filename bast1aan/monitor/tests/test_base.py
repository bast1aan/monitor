from bast1aan.monitor.base import PingCommand, IPV4, IPV6, CommandSet


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
    assert str(result.command) == 'ping -c 1 fliepsflops'

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

def test_commandset():
    command_set = CommandSet(
        PingCommand('localhost', only=IPV4),
        PingCommand('localhost', only=IPV6),
        PingCommand('flupflops'),
        PingCommand('127.0.0.1', only=IPV6),
        PingCommand('127.0.0.1', only=IPV4),
    )
    result_set = [result for result in command_set()]
    assert tuple(bool(result) for result in result_set) == (True, True, False, False, True)

    assert '64 bytes from localhost (127.0.0.1): icmp_seq=1' in str(result_set[0])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_set[0])

    assert '64 bytes from localhost (::1): icmp_seq=1' in str(result_set[1])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_set[1])

    assert 'flupflops: Name or service not known' in str(result_set[2])
    assert 'ping -c 1 flupflops' == str(result_set[2].command)

    assert '127.0.0.1: Address family for hostname not supported' in str(result_set[3])
    assert 'ping -c 1 -6 127.0.0.1' == str(result_set[3].command)

    assert '64 bytes from 127.0.0.1: icmp_seq=1' in str(result_set[4])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_set[4])
