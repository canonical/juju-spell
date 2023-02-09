from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

PING_ACCESSIBLE = "accessible"
PING_UNREACHABLE = "unreachable"


class PingCommand(BaseJujuCommand):
    async def execute(self, controller: Controller, **kwargs) -> str:
        """Check if controller is connected."""
        connected = controller.is_connected()
        self.logger.debug("%s is connected '%r'", controller.controller_uuid, connected)
        return PING_ACCESSIBLE if connected else PING_UNREACHABLE
