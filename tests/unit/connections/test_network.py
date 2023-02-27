import socket
import subprocess
import unittest
from unittest import mock

import pytest

from juju_spell.config import Connection


@pytest.mark.parametrize("return_code, exp_result", [(1, True), (0, False)])
@mock.patch("juju_spell.connections.network.socket.socket")
def test_is_port_free(mock_socket, return_code, exp_result):
    """Test function checking if port is free."""
    from juju_spell.connections.network import _is_port_free

    test_port = 17070
    mock_socket.return_value = tcp = mock.MagicMock()
    tcp.connect_ex.return_value = return_code

    result = _is_port_free(test_port)

    assert result == exp_result
    mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
    tcp.connect_ex.assert_called_once_with(("localhost", test_port))
    tcp.close.assert_called_once()


@mock.patch("juju_spell.connections.network._is_port_free")
@mock.patch("juju_spell.connections.network.random.shuffle")
def test_get_free_tcp_port(mock_random_shuffle, mock_is_port_free):
    """Test getting free TCP port."""
    from juju_spell.connections.network import get_free_tcp_port

    exp_port = 17073
    mock_is_port_free.side_effect = [False, False, True, False]

    port = get_free_tcp_port(range(17071, 17075))

    mock_random_shuffle.assert_called_once_with([17071, 17072, 17073, 17074])
    mock_is_port_free.assert_has_calls([mock.call(17071), mock.call(17072), mock.call(17073)])
    assert port == exp_port


@mock.patch("juju_spell.connections.network._is_port_free")
def test_get_free_tcp_port_exception(mock_is_port_free):
    """Test getting free TCP port raising an Error."""
    from juju_spell.connections.network import get_free_tcp_port

    mock_is_port_free.return_value = False

    with pytest.raises(ValueError):
        get_free_tcp_port(range(17071, 17075))


def test_empty_connection():
    """Test EmptyConnection."""
    from juju_spell.connections.network import EmptyConnection

    connection = EmptyConnection()
    assert connection.is_connected is False
    connection.connect()
    assert connection.is_connected is True
    connection.clean()
    assert connection.is_connected is False


class EmptyConnectionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        from juju_spell.connections.network import EmptyConnection

        self.connection = EmptyConnection()

    def test_is_connected(self):
        """Test is_connected."""
        self.assertFalse(self.connection.is_connected)
        self.connection._connected = True
        self.assertTrue(self.connection.is_connected)

    def test_connect(self):
        """Test connect function."""
        self.assertFalse(self.connection._connected)
        self.connection.connect()
        self.assertTrue(self.connection._connected)

    def test_clean(self):
        """Test clean function."""
        self.connection._connected = True
        self.assertTrue(self.connection._connected)
        self.connection.clean()
        self.assertFalse(self.connection._connected)


class BaseSubprocessConnectionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        from juju_spell.connections.network import BaseSubprocessConnection

        self.connection = BaseSubprocessConnection()

    def test_is_connected(self):
        """Test is_connected."""
        self.assertFalse(self.connection.is_connected)
        self.connection.process = mock.MagicMock()
        self.assertTrue(self.connection.is_connected)

    def test_connect(self):
        """Test connect function."""
        with pytest.raises(NotImplementedError):
            self.connection.connect()

    def test_clean(self):
        """Test clean function."""
        self.connection.process = mocked_process = mock.MagicMock()
        self.connection.clean()
        mocked_process.terminate.assert_called_once()


@pytest.mark.parametrize(
    "args, exp_cmd",
    [
        (
            ("localhost:1234", "10.1.1.99:17070", "bastion"),
            ["ssh", "bastion", "-N", "-L", "localhost:1234:10.1.1.99:17070"],
        ),
        (
            ("localhost:1234", "10.1.1.99:17070", "bastion", ["bastion1", "bastion2"]),
            [
                "ssh",
                "bastion",
                "-N",
                "-L",
                "localhost:1234:10.1.1.99:17070",
                "-J bastion1 -J bastion2",
            ],
        ),
        (
            ("1234", "10.1.1.99:17070", "ubuntu@bastion"),
            ["ssh", "ubuntu@bastion", "-N", "-L", "1234:10.1.1.99:17070"],
        ),
    ],
)
@mock.patch("juju_spell.connections.network.subprocess.Popen", return_value=mock.MagicMock)
def test_ssh_port_forwarding_proc_connect(mock_popen, args, exp_cmd):
    """Test create ssh tune for port forwarding."""
    mock_popen.return_value = mock_process = mock.MagicMock()
    mock_process.returncode.return_value = 0
    from juju_spell.connections.network import SshPortForwardSubprocess

    ssh_portforward = SshPortForwardSubprocess(*args)
    ssh_portforward.connect()

    assert ssh_portforward.is_connected is True
    mock_popen.assert_called_once_with(exp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize(
    "args, exp_cmd",
    [
        ((["10.1.1.0/24"], "bastion"), ["sshuttle", "10.1.1.0/24", "-r", "bastion"]),
        (
            (["10.1.1.0/24"], "bastion", ["bastion1", "bastion2"]),
            [
                "sshuttle",
                "10.1.1.0/24",
                "-r",
                "bastion",
                "-e 'ssh -J bastion1 -J bastion2'",
            ],
        ),
        (
            (["10.1.1.0/24", "20.1.1.0/24"], "ubuntu@bastion"),
            ["sshuttle", "10.1.1.0/24", "20.1.1.0/24", "-r", "ubuntu@bastion"],
        ),
    ],
)
@mock.patch("juju_spell.connections.network.subprocess.Popen")
def test_sshuttle_proc(mock_popen, args, exp_cmd):
    """Test create sshuttle connection."""
    from juju_spell.connections.network import SshuttleSubprocess

    sshuttle = SshuttleSubprocess(*args)
    sshuttle.connect()

    mock_popen.assert_called_once_with(exp_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.mark.parametrize(
    "endpoint, connection, sshuttle, exp_endpoint",
    [
        ("10.1.1.1:17070", None, False, "10.1.1.1:17070"),
        ("10.1.1.1:17070", Connection("10.2.2.1"), False, "localhost:18070"),
        ("10.1.1.1:17070", Connection("10.2.2.1"), True, "10.1.1.1:17070"),
    ],
)
@mock.patch("juju_spell.connections.network.get_free_tcp_port", return_value=18070)
@mock.patch("juju_spell.connections.network.SshPortForwardSubprocess")
@mock.patch("juju_spell.connections.network.SshuttleSubprocess")
def test_get_connection(
    mocked_sshuttle,
    mocked_port_forward,
    _,
    endpoint,
    connection,
    sshuttle,
    exp_endpoint,
):
    """Test get connection."""
    controller_config = mock.MagicMock()
    controller_config.endpoint = endpoint
    controller_config.connection = connection
    from juju_spell.connections.network import get_connection

    controller_endpoint, _ = get_connection(controller_config, sshuttle=sshuttle)

    assert controller_endpoint == exp_endpoint
    if connection and not sshuttle:
        mocked_port_forward.assert_called_once()
        mocked_sshuttle.assert_not_called()
    elif connection and sshuttle:
        mocked_port_forward.assert_not_called()
        mocked_sshuttle.assert_called_once()
    else:
        mocked_port_forward.assert_not_called()
        mocked_sshuttle.assert_not_called()
