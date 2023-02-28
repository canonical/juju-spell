from typing import Dict, List, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand


class ListModelsCommand(BaseJujuCommand):
    async def execute(
        self, controller: Controller, **kwargs
    ) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        outputs = {"refresh": False, "models": []}
        if kwargs["refresh"]:
            outputs["refresh"] = True
            outputs["models"] = await controller.list_models()
        else:
            outputs["models"] = ["TODO: read from cache; not implemented."]
        self.logger.debug(
            "Listing models in '%s': %s", controller.controller_uuid, outputs["models"]
        )
        return outputs
