"""List models from the local cache or from the controllers."""
from logging import Logger
from time import time
from typing import Any, Dict, List, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.exceptions import JujuSpellError
from juju_spell.utils import Cache, load_from_cache, save_to_cache


class ListModelsCommand(BaseJujuCommand):
    """Command to list models from the local cache or from the controllers."""

    async def execute(self, controller: Controller, **kwargs: Any) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        cache: Union[None, Cache] = None

        if not kwargs["refresh"]:
            fname = f"{self.name}_{kwargs['controller_config'].uuid}"
            cache = load_cache_data(fname, self.logger, kwargs["controller_config"].uuid)

        if kwargs["refresh"] or cache is None:
            models = list(
                await self.get_filtered_model_names(
                    controller=controller,
                    models=None,
                    model_mappings=kwargs["controller_config"].model_mapping,
                )
            )
            cache = save_cache_data(controller, models, kwargs["refresh"], self.logger, self.name)

        self.logger.debug("%s list models: %s", controller.controller_uuid, cache.data["models"])
        return cache.context


def save_cache_data(
    controller: Controller, models: List[str], refresh: bool, logger: Logger, command_name: str
) -> Cache:
    """Gracefully save cache data to default cache directory."""
    cache = Cache(
        uuid=controller.controller_uuid,
        name=controller.controller_name,
        data={
            "models": models,
            "refresh": refresh,
        },
        timestamp=time(),
    )
    fname = f"{command_name}_{controller.controller_uuid}"
    error_message_template = "%s list models failed to save cache: %s."
    try:
        save_to_cache(cache, fname)
        logger.debug(
            "%s list models: save result to cache `%s`", controller.controller_uuid, str(fname)
        )
    except JujuSpellError as error:
        logger.warning(error_message_template, controller.controller_uuid, str(error))
    return cache


def load_cache_data(fname: str, logger: Logger, uuid: str) -> Union[None, Cache]:
    """Gracefully load cache data from default cache directory."""
    cache = None
    error_message_template = "%s list models failed to load cache: %s."
    try:
        cache = load_from_cache(fname)
        cache.data["refresh"] = False
        logger.debug("%s list models: load result from cache `%s`", uuid, str(fname))
    except JujuSpellError as error:
        logger.warning(error_message_template, uuid, str(error))
    return cache
