"""Command to get status of models."""
from typing import Any, Dict, List, Optional

from juju.client._definitions import FullStatus
from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand


class StatusCommand(BaseJujuCommand):
    """Command to show status for models."""

    async def execute(
        self, controller: Controller, *args: Any, models: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, FullStatus]:
        """Get status for selected models in controller."""
        output = {}
        async for name, model in self.get_filtered_models(
            controller=controller,
            models=models,
            model_mappings=kwargs["controller_config"].model_mapping,
        ):
            status = await model.get_status()
            self.logger.debug("%s model %s status: %s", controller.controller_uuid, name, status)
            output[name] = status

        return output
