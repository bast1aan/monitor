from typing import ClassVar

from bast1aan.monitor import PingCommand, IPV4, IPV6, CommandSet, DependingCommandSet, ANY_SUCCEEDS, try_until_succeeds


def test_ping_success() -> None:
    ping_command = PingCommand('localhost')
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (::1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg

def test_ping_failure() -> None:
    ping_command = PingCommand('fliepsflops')
    result = ping_command()
    assert bool(result) is False
    msg = str(result)
    assert 'fliepsflops: Name or service not known' in msg
    assert str(result.command) == 'ping -c 1 fliepsflops'

def test_ping_ipv4_success() -> None:
    ping_command = PingCommand('localhost', only=IPV4)
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (127.0.0.1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg

def test_ping_ipv6_success() -> None:
    ping_command = PingCommand('localhost', only=IPV6)
    result = ping_command()
    assert bool(result) is True
    msg = str(result)
    assert '64 bytes from localhost (::1): icmp_seq=1' in msg
    assert '1 packets transmitted, 1 received, 0% packet loss' in msg

def test_commandset() -> None:
    command1 = PingCommand('localhost', only=IPV4)
    command2 = PingCommand('localhost', only=IPV6)
    command3 = PingCommand('flupflops')
    command4 = PingCommand('127.0.0.1', only=IPV6)
    command5 = PingCommand('127.0.0.1', only=IPV4)

    command_set = CommandSet(command1, command2, command3, command4, command5)
    result_set = command_set()
    result_map = {result.command: result for result in result_set}
    assert {k: bool(v) for k, v in result_map.items()} == {command1: True, command2: True, command3: False, command4: False, command5: True}

    assert '64 bytes from localhost (127.0.0.1): icmp_seq=1' in str(result_map[command1])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_map[command1])

    assert '64 bytes from localhost (::1): icmp_seq=1' in str(result_map[command2])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_map[command2])

    assert 'flupflops: Name or service not known' in str(result_map[command3])
    assert 'ping -c 1 flupflops' == str(result_map[command3].command)

    assert '127.0.0.1: Address family for hostname not supported' in str(result_map[command4])
    assert 'ping -c 1 -6 127.0.0.1' == str(result_map[command4].command)

    assert '64 bytes from 127.0.0.1: icmp_seq=1' in str(result_map[command5])
    assert '1 packets transmitted, 1 received, 0% packet loss' in str(result_map[command5])

    assert bool(result_set) is False

def test_commandset_any_succeeds() -> None:
    command1 = PingCommand('localhost', only=IPV4)
    command2 = PingCommand('localhost', only=IPV6)
    command3 = PingCommand('flupflops')
    command4 = PingCommand('127.0.0.1', only=IPV6)
    command5 = PingCommand('127.0.0.1', only=IPV4)

    command_set = CommandSet(command1, command2, command3, command4, command5, succeeds_if=ANY_SUCCEEDS)
    result_set = command_set()
    assert bool(result_set) is True

def test_commandset_success() -> None:
    command_set = CommandSet(
        PingCommand('localhost', only=IPV4),
        PingCommand('localhost', only=IPV6),
        PingCommand('127.0.0.1', only=IPV4),
    )

    result_set = command_set()

    assert bool(result_set) is True

def test_nested_commandset() -> None:
    command_set = CommandSet(
        CommandSet(
            PingCommand('localhost', only=IPV4),
            PingCommand('localhost', only=IPV6),
        ),
        PingCommand('127.0.0.1', only=IPV4),
    )

    result_set = command_set()

    assert bool(result_set) is True

def test_depending_commandset_success() -> None:
    command_set = CommandSet(
        DependingCommandSet(
            dep1_command1 := PingCommand('localhost', only=IPV4),
            if_succeeds=CommandSet(
                dep1_success_command1 := PingCommand('localhost', only=IPV6),
                dep1_success_command2 := PingCommand('127.0.0.1', only=IPV4),
                dep1_success_command3 := PingCommand('127.0.0.1', only=IPV6),
                dep1_success_command4 := PingCommand('::1', only=IPV6),
            )
        ),
        DependingCommandSet(
            dep2_command1 := PingCommand('nonexistent'),
            if_succeeds=CommandSet(
                dep2_success_command1 := PingCommand('127.0.0.2', only=IPV4),
                dep2_success_command2 := PingCommand('127.0.0.2', only=IPV6),
            )
        ),
    )

    result_set = command_set()
    results = [(result.command, bool(result)) for result in result_set]

    assert (dep1_command1, True) in results and (dep2_command1, False) in results, \
        "First 2 commands that have been executed should be always available"

    assert (dep1_success_command1, True) in results
    assert (dep1_success_command2, True) in results
    assert (dep1_success_command3, False) in results
    assert (dep1_success_command4, True) in results

    assert (dep2_success_command1, True) not in results
    assert (dep2_success_command2, False) not in results

def test_depending_commandset_fail() -> None:
    command_set = CommandSet(
        DependingCommandSet(
            dep1_command1 := PingCommand('localhost', only=IPV4),
            if_fails=CommandSet(
                dep1_success_command1 := PingCommand('localhost', only=IPV6),
                dep1_success_command2 := PingCommand('127.0.0.1', only=IPV4),
                dep1_success_command3 := PingCommand('127.0.0.1', only=IPV6),
                dep1_success_command4 := PingCommand('::1', only=IPV6),
            )
        ),
        DependingCommandSet(
            dep2_command1 := PingCommand('nonexistent'),
            if_fails=CommandSet(
                dep2_success_command1 := PingCommand('127.0.0.2', only=IPV4),
                dep2_success_command2 := PingCommand('127.0.0.2', only=IPV6),
            )
        ),
    )

    result_set = command_set()
    results = [(result.command, bool(result)) for result in result_set]

    assert (dep1_command1, True) in results and (dep2_command1, False) in results, \
        "First 2 commands that have been executed should be always available"

    assert (dep1_success_command1, True) not in results
    assert (dep1_success_command2, True) not in results
    assert (dep1_success_command3, False) not in results
    assert (dep1_success_command4, True) not in results

    assert (dep2_success_command1, True) in results
    assert (dep2_success_command2, False) in results

    assert bool(result_set) is False

def test_depending_commandset_fail_eventually_succeeds() -> None:
    command_set = DependingCommandSet(
        PingCommand('nonexistent-so-will-fail'),
        if_fails=CommandSet(
            PingCommand('127.0.0.1', only=IPV4),
        ),
        succeeds_if=ANY_SUCCEEDS
    )

    result_set = command_set()

    assert bool(result_set) is True

def test_try_until_succeeds_one_succeeds() -> None:
    command_set = try_until_succeeds(
        cmd1 := PingCommand('nonexistent-so-will-fail'),
        cmd2 := PingCommand('127.0.0.1', only=IPV4),
        cmd3 := PingCommand('127.0.0.1', only=IPV4),
    )

    result = command_set()

    assert bool(result) is True

def test_try_until_succeeds_all_fail() -> None:
    command_set = try_until_succeeds(
        cmd1 := PingCommand('nonexistent-so-will-fail'),
        cmd2 := PingCommand('127.0.0.1', only=IPV6),
        cmd3 := PingCommand('127.0.0.1', only=IPV6),
    )

    result = command_set()

    assert bool(result) is False


def test_try_until_succeeds_with_count_3_succeeds() -> None:
    from bast1aan.monitor.base import AsyncCommand, _CommandResult

    class OnlySecondSucceeds(AsyncCommand):
        _cnt: ClassVar[int] = 0
        @staticmethod
        def reset() -> None:
            OnlySecondSucceeds._cnt = 0
        async def run(self) -> _CommandResult:
           OnlySecondSucceeds._cnt += 1
           return _CommandResult(
               OnlySecondSucceeds._cnt == 2,
               str(self),
               self
           )
        def __str__(self) -> str:
            return f"{OnlySecondSucceeds._cnt=}"
        def __hash__(self) -> int:
            return hash((self, OnlySecondSucceeds._cnt))

    cmd = OnlySecondSucceeds()

    assert bool(cmd()) is False
    assert bool(cmd()) is True
    assert bool(cmd()) is False

    assert OnlySecondSucceeds._cnt == 3, "All three have been executed"

    OnlySecondSucceeds.reset()

    command_set = try_until_succeeds(
        OnlySecondSucceeds(),
        count=3
    )

    command_result = command_set()

    assert bool(command_result) is True

    assert OnlySecondSucceeds._cnt == 2, "Only the first 2 have been executed, because the second succeeded"
