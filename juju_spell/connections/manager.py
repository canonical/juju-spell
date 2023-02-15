import asyncio
import dataclasses
import logging
import time
from typing import Dict, Union
from uuid import UUID

from juju import juju
from juju.errors import JujuConnectionError

from juju_spell.config import Controller
from juju_spell.connections.network import BaseConnection, get_connection
from juju_spell.settings import (
    DEFAULT_CONNECTIN_TIMEOUT,
    DEFAULT_RETRY_BACKOFF,
    DEFUALT_MAX_FRAME_SIZE,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Connection:
    controller: juju.Controller
    connection_process: BaseConnection


def _get_wait_time(attempt: int, retry_backoff: Union[int, float]) -> float:
    """Calculate wait time for reconnection."""
    return retry_backoff ** (attempt - 2)  # exponential wait y^(x-2)


async def controller_direct_connection(
    controller: juju.Controller,
    uuid: UUID,
    name: str,
    endpoint: str,
    username: str,
    password: str,
    cacert: str,
):
    """Direct connection to controller without JUJU_DATA.

    This is a helper function for connecting to a controller with simple exponential
    retry and with fix for missing controller_name and controller_uuid.
    """
    start = time.time()
    attempt: int = 0
    while True:
        try:
            await controller._connector.connect(
                endpoint=endpoint,
                username=username,
                password=password,
                cacert=cacert,
                retries=0,  # disable retires in connection
                retry_backoff=0,
            )
            controller._connector.controller_uuid = uuid
            controller._connector.controller_name = name
            break
        except JujuConnectionError:
            # Note(rgildein): Connection will raise JujuConnectionError if endpoint
            # is unreachable. This can happen, for example, when port forwarding is
            # through a subprocess and the process has not yet started.
            logger.info("%s connection to controller %s failed", uuid, name)
            wait = _get_wait_time(attempt, DEFAULT_RETRY_BACKOFF)
            await asyncio.sleep(wait)
            if time.time() - start >= DEFAULT_CONNECTIN_TIMEOUT:
                raise

            attempt += 1
            continue
        except Exception as error:
            logger.info(
                "%s connection to controller %s failed with error '%s'",
                uuid,
                name,
                error,
            )
            raise


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
        self, controller_config: Controller, sshuttle: bool = False
    ) -> juju.Controller:
        """Prepare connection to Controller and return it."""
        logger.info("getting a new connection to controller %s", controller_config.name)
        controller = juju.Controller(max_frame_size=DEFUALT_MAX_FRAME_SIZE)
        controller_endpoint, connection_process = get_connection(
            controller_config, sshuttle
        )
        connection_process.connect()
        self.connections[controller_config.name] = Connection(
            controller, connection_process
        )
        await controller_direct_connection(
            controller,
            uuid=controller_config.uuid,
            name=controller_config.name,
            endpoint=controller_endpoint,
            username=controller_config.user,
            password=controller_config.password,
            cacert=controller_config.ca_cert,
        )
        logger.info("controller %s was connected", controller.controller_name)
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

        return await self._connect(controller_config, sshuttle)
