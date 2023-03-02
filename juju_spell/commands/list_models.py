"""List models from the local cache or from the controllers."""
from logging import Logger
from time import time
from typing import Any, Dict, List, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.exceptions import JujuSpellError
from juju_spell.utils import load_from_cache, save_to_cache


class ListModelsCommand(BaseJujuCommand):
    """Command to list models from the local cache or from the controllers."""

    async def execute(
        self, controller: Controller, *args: Any, **kwargs: Any
    ) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        outputs: Union[JujuSpellError, Dict[str, Any]] = {}

        if not kwargs["refresh"]:
            outputs = load_cache_data(kwargs["controller_config"].uuid, self.logger)

        if kwargs["refresh"] or isinstance(outputs, JujuSpellError):
            models = list(
                await self.get_filtered_model_names(
                    controller=controller,
                    models=None,
                    model_mappings=kwargs["controller_config"].model_mapping,
                )
            )
            outputs = save_cache_data(controller, models, kwargs["refresh"], self.logger)

        self.logger.debug("%s list models: %s", controller.controller_uuid, outputs["models"])
        return outputs


def save_cache_data(
    controller: Controller, models: List[str], refresh: bool, logger: Logger
) -> Dict[str, Any]:
    """Gracefully save cache data to default cache directory."""
    cache_data = {
        "uuid": controller.controller_uuid,
        "name": controller.controller_name,
        "models": models,
        "refresh": refresh,
        "timestamp": time(),
    }
    error_message_template = "%s list models failed to save cache: %s."
    try:
        save_to_cache(cache_data, controller.controller_uuid)
    except JujuSpellError as error:
        logger.debug(error_message_template, controller.controller_uuid, str(error))
    return cache_data


def load_cache_data(uuid: str, logger: Logger) -> Union[JujuSpellError, Dict[str, Any]]:
    """Gracefully load cache data from default cache directory."""
    error_message_template = "%s list models failed to load cache: %s."
    try:
        cache_data = load_from_cache(uuid)
        cache_data["refresh"] = False
    except JujuSpellError as error:
        logger.debug(error_message_template, uuid, str(error))
        return JujuSpellError(error_message_template.format(uuid, str(error)))
    return cache_data
