"""List models from the local cache or from the controllers."""
from typing import Any, Dict, List, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand


class ListModelsCommand(BaseJujuCommand):
    """Command to list models from the local cache or from the controllers."""

    async def execute(
        self, controller: Controller, *args: Any, **kwargs: Any
    ) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        outputs = {
            "refresh": kwargs["refresh"],
            "models": list(
                await self.get_filtered_model_names(
                    controller=controller,
                    models=None,
                    model_mappings=kwargs["controller_config"].model_mapping,
                )
            )
            if kwargs["refresh"]
            else ["TODO: read from cache; not implemented."],
        }
        self.logger.debug("%s list models: %s", controller.controller_uuid, outputs["models"])
        return outputs
