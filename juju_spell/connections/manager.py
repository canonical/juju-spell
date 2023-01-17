import dataclasses
import logging
from typing import Dict

from juju import juju

from juju_spell.config import Controller
from juju_spell.connections.network import BaseConnection, get_connection
from juju_spell.settings import JUJUSPELL_DEFAULT_PORT_RANGE

logger = logging.getLogger(__name__)

MAX_FRAME_SIZE = 6**24


@dataclasses.dataclass
class Connection:
    controller: juju.Controller
    connection_process: BaseConnection


class ConnectManager(object):
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
    _connections = {}

    def __new__(cls):
        if getattr(cls, "_manager") is None:
            cls._manager = super(ConnectManager, cls).__new__(cls)

        return cls._manager

    @property
    def connections(self) -> Dict[str, Connection]:
        """Return list of connections ."""
        return self._connections

    async def _connect(
        self, controller_config: Controller, port_range: range, sshuttle: bool = False
    ) -> juju.Controller:
        """Prepare connection to Controller and return it."""
        logger.info("getting a new connection to controller %s", controller_config.name)
        controller = juju.Controller(max_frame_size=MAX_FRAME_SIZE)
        controller_endpoint, connection_process = get_connection(
            controller_config, port_range, sshuttle
        )
        connection_process.connect()

        await controller.connect(
            endpoint=controller_endpoint,
            username=controller_config.username,
            password=controller_config.password,
            cacert=controller_config.ca_cert,
        )
        logger.info("controller %s was connected", controller.controller_name)
        self.connections[controller_config.name] = Connection(
            controller, connection_process
        )
        return controller

    async def clean(self):
        """Close all connections."""
        for name in self.connections.keys():
            connection = self.connections[name]
            await connection.controller.disconnect()  # disconnect controller
            connection.connection_process.clean()  # clean connection process
            logger.info(
                "%s connection was closed", connection.controller.controller_uuid
            )

        self.connections.clear()

    async def get_controller(
        self,
        controller_config: Controller,
        port_range: range = JUJUSPELL_DEFAULT_PORT_RANGE,
        sshuttle: bool = False,
        reconnect: bool = False,
    ) -> juju.Controller:
        """Get controller."""
        assert isinstance(
            controller_config, Controller
        ), "Not supported format of controller config"

        connection = self.connections.get(controller_config.name)
        if connection and connection.controller.is_connected() and not reconnect:
            logger.info(
                "%s using controller from cache", connection.controller.controller_uuid
            )
            return connection.controller
        elif connection and reconnect:
            await connection.controller.disconnect()

        return await self._connect(controller_config, port_range, sshuttle)
