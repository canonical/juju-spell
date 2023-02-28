"""Command to show controllers information."""
from typing import Any

from juju.client._definitions import ControllerAPIInfoResults
from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand


class ShowControllerCommand(BaseJujuCommand):
    """Command to show a controller."""

    async def execute(
        self,
        controller: Controller,
        *args: Any,
        **kwargs: Any,
    ) -> ControllerAPIInfoResults:
        """Execute main code.

        Changed name because this has to override base_command.
        """
        info = await controller.info()
        self.logger.debug("%s info: %s", controller.controller_uuid, info)
        return info
