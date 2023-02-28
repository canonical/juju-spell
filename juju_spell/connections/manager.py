"""Module for managing connection to controllers."""
import dataclasses
import logging
from typing import Dict, Union

from juju import juju

from juju_spell.config import Controller
from juju_spell.connections.conn_builder import build_controller_conn
from juju_spell.connections.network import BaseConnection, get_connection
from juju_spell.settings import DEFAULT_MAX_FRAME_SIZE

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Connection:
    """Representation of connection."""

    controller: juju.Controller
    connection_process: BaseConnection


def _get_wait_time(attempt: int, retry_backoff: Union[int, float]) -> float:
    """Calculate wait time for reconnection."""
    return retry_backoff ** (attempt - 2)  # exponential wait y^(x-2)


class ConnectManager:
    """Connect manager is used to define connections for controllers.

    Usage
        example 1

        ```python
        async def task(...):
            ...
            connect_manager = ConnectManager():
            controller = await connect_manager.get_controller(controller_config)
            ...
        ```

        example 2

        ```python
        from juju_spell.connection import connect_manager

        async def task1(...):
            ...
            controller = await connect_manager.get_controller(controller_config)
            ...

        async def task2(...):
            ...
            # return same controller
            controller = await connect_manager.get_controller(controller_config)
            ...
        ```
    """

    _manager = None
    _connections: Dict[str, Connection] = {}

    def __new__(cls) -> "ConnectManager":
        if cls._manager is None:
            cls._manager = super(ConnectManager, cls).__new__(cls)

        return cls._manager

    @property
    def connections(self) -> Dict[str, Connection]:
        """Return list of connections ."""
        return self._connections

    async def _connect(
        self, controller_config: Controller, sshuttle: bool = False
    ) -> juju.Controller:
        """Prepare connection to Controller and return it."""
        logger.info("getting a new connection to controller %s", controller_config.name)
        controller = juju.Controller(max_frame_size=DEFAULT_MAX_FRAME_SIZE)
        controller_endpoint, connection_process = get_connection(controller_config, sshuttle)
        connection_process.connect()
        self.connections[controller_config.name] = Connection(controller, connection_process)
        await build_controller_conn(
            controller,
            uuid=controller_config.uuid,
            name=controller_config.name,
            endpoint=controller_endpoint,
            username=controller_config.user,
            password=controller_config.password,
            cacert=controller_config.ca_cert,
            retry_policy=controller_config.retry_policy,
        )
        logger.info("controller %s was connected", controller.controller_name)
        return controller

    async def clean(self) -> None:
        """Close all connections."""
        for connection in self.connections.values():
            await connection.controller.disconnect()  # disconnect controller
            connection.connection_process.clean()  # clean connection process
            logger.info("%s connection was closed", connection.controller.controller_uuid)

        self.connections.clear()

    async def get_controller(
        self,
        controller_config: Controller,
        sshuttle: bool = False,
        reconnect: bool = False,
    ) -> juju.Controller:
        """Get controller."""
        assert isinstance(
            controller_config, Controller
        ), "Not supported format of controller config"

        connection = self.connections.get(controller_config.name)
        controller = None
        if connection and connection.controller.is_connected() and not reconnect:
            logger.info("%s using controller from cache", connection.controller.controller_uuid)
            controller = connection.controller
        elif connection and reconnect:
            await connection.controller.disconnect()

        return controller or await self._connect(controller_config, sshuttle)
