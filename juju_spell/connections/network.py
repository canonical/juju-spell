"""Module handling connection to remote cloud."""
import abc
import logging
import random
import socket
import subprocess
from typing import List, Optional, Tuple

from juju_spell.config import Controller

logger = logging.getLogger(__name__)


def _is_port_free(port: int) -> bool:
    """Check if port is free to use."""
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = tcp.connect_ex(("localhost", port))
    tcp.close()
    return result != 0


def get_free_tcp_port(port_range: range) -> int:
    """Get free TCP port from range.

    This function will return free port on local system. This port will be used to
    port-forward remote controller to localhost:<port>.
    """
    list_of_ports = list(port_range)
    random.shuffle(list_of_ports)  # randomly shuffle list of ports

    for port in list_of_ports:
        if _is_port_free(port):
            logger.debug("free port %d was found", port)
            return port

    raise ValueError(f"Could not find a free port in range {port_range}")


class BaseConnection(metaclass=abc.ABCMeta):
    """Base connection."""

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:  # pragma: no cover
        """Return True if connection is alive."""

    @abc.abstractmethod
    def connect(self) -> None:  # pragma: no cover
        """Create connection.

        This function is responsible for any port-forwarding, sshuttle tunnelling, etc.
        """

    @abc.abstractmethod
    def clean(self) -> None:  # pragma: no cover
        """Clean/terminate/close connection."""


class EmptyConnection(BaseConnection):
    """Empty connection for controller with direct access."""

    def __init__(self) -> None:
        """Initialize the connection."""
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> None:
        self._connected = True

    def clean(self) -> None:
        self._connected = False


class BaseSubprocessConnection(BaseConnection):
    """Base connection using subprocess."""

    def __init__(self) -> None:
        """Define empty process."""
        self.process: Optional[subprocess.Popen] = None

    @property
    def is_connected(self) -> bool:
        if self.process is None or self.process.returncode is None:
            # process is already killed or was never created
            return False

        return True

    def connect(self) -> None:
        raise NotImplementedError

    def clean(self) -> None:
        """Terminate connection subprocess."""
        if self.process is not None:
            self.process.terminate()


class SshPortForwardSubprocess(BaseSubprocessConnection):
    """Shh port-forwarding connection with usage of subprocess."""

    def __init__(
        self,
        local_target: str,
        remote_target: str,
        destination: str,
        jumps: Optional[List[str]] = None,
    ):
        """Configure SshPortForward subprocess.

        Example:
        Call this object as follows
        ```python
        connection = SshPortForwardSubprocess(
            "localhost:17071", "10.1.1.99:17070", "gandalf@customer", ["bastion"]
        )
        connection.connect()
        ...
        connection.clean()
        ```
        is equivalent to
        ```bash
        ssh -N -L localhost:17071:10.1.1.99:17070 -J bastion gandalf@customer
        ```
        and it will port-forward the `10.1.1.99:17070` to `localhost:17071`.

        :param local_target: bind_address:port to which remote target will be
                             port-forwarded
        :param remote_target: remote host and port, which will be port-forwarded
        :param destination: ssh destination, which may be specified as either
                            [user@]hostname or a URI of the form
                            `ssh://[user@]hostname[:port]`
        :param jumps: connect to the destination by first making a ssh connection via
                      list of jumps host described by destination
        """
        super().__init__()
        self.local_target = local_target
        self.remote_target = remote_target
        self.destination = destination
        self.jumps = jumps

    def connect(self) -> None:
        """Create ssh tunnel."""
        logger.info(
            "port forwarding %s to %s via %s",
            self.remote_target,
            self.local_target,
            self.destination,
        )
        cmd = [
            "ssh",
            self.destination,
            "-N",
            "-L",
            f"{self.local_target}:{self.remote_target}",
        ]
        if self.jumps:
            cmd.append(" ".join(f"-J {jump}" for jump in self.jumps))

        logger.debug("cmd `%s` will be executed", cmd)
        # pylint: disable=R1732
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class SshuttleSubprocess(BaseSubprocessConnection):
    """Sshuttle connection with usage of subprocess."""

    def __init__(self, subnets: List[str], destination: str, jumps: Optional[List[str]] = None):
        """Configure Sshuttle subprocess.

        Example:
        Call this function as follows
        ```python
        connection = SshuttleSubprocess(
            ["10.1.1.0/24"], "gandalf@customer", ["bastion"]
        )
        connection.connect()
        ...
        connection.clean()
        ```
        is equivalent to
        ```bash
        sshuttle -r gandalf@customer -e 'ssh -J bastion' 10.1.1.0/24
        ```
        and it will create ssh tunnel and add subnetworks to iptables. This will
        redirect all traffic to subnets through this tunnel.

        :param subnets: capture and forward traffic to these subnets
        :param destination: ssh hostname (and optional username and password) of remote
                            sshuttle server [USERNAME[:PASSWORD]@]ADDR[:PORT]
        :param jumps: connect to the destination by first making a ssh connection via
                      list of jumps host described by destination
        """
        super().__init__()
        self.subnets = subnets
        self.destination = destination
        self.jumps = jumps

    def connect(self) -> None:
        """Create sshuttle tunnel."""
        logger.info("sshuttle %s subnets via %s", self.subnets, self.destination)
        cmd = ["sshuttle", *self.subnets, "-r", self.destination]
        if self.jumps:
            jumps_option = " ".join(f"-J {jump}" for jump in self.jumps)
            cmd.append(f"-e 'ssh {jumps_option}'")

        logger.debug("cmd `%s` will be executed", cmd)
        # pylint: disable=R1732
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def get_connection(
    controller_config: Controller,
    sshuttle: bool = False,
) -> Tuple[str, BaseConnection]:
    """Get connection."""
    controller_endpoint = controller_config.endpoint
    process: BaseConnection = EmptyConnection()  # controller has direct access

    if not controller_config.connection:
        logger.debug("skip, due missing connection in the configuration")
    elif not sshuttle:
        port = get_free_tcp_port(controller_config.connection.port_range)
        controller_endpoint = f"localhost:{port}"
        process = SshPortForwardSubprocess(
            controller_endpoint,
            controller_config.endpoint,
            controller_config.connection.destination,
            controller_config.connection.jumps,
        )
    elif sshuttle and controller_config.connection.subnets:
        process = SshuttleSubprocess(
            controller_config.connection.subnets,
            controller_config.connection.destination,
            controller_config.connection.jumps,
        )

    return controller_endpoint, process
