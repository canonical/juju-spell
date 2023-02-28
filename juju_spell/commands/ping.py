"""Command to check connection to controllers."""
from typing import Any

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand


class PingCommand(BaseJujuCommand):
    """Ping command."""

    async def execute(self, controller: Controller, *args: Any, **kwargs: Any) -> str:
        """Check if controller is connected."""
        connected = controller.is_connected()
        self.logger.debug("%s is connected '%r'", controller.controller_uuid, connected)
        return "accessible" if connected else "unreachable"
