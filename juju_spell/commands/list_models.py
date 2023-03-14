"""List models from the local cache or from the controllers."""
from time import time
from typing import Any, Dict, List, Optional, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.exceptions import JujuSpellError
from juju_spell.utils import FileCache


class ListModelsCommand(BaseJujuCommand):
    """Command to list models from the local cache or from the controllers."""

    async def execute(
        self, controller: Controller, *args: Any, **kwargs: Any
    ) -> Dict[str, Union[List, bool]]:
        """List models from the local cache or from the controllers."""
        file_cache: Union[None, FileCache] = None

        if not kwargs["refresh"]:
            file_cache = self.load_cache_data(controller)

        if kwargs["refresh"] or file_cache is None or file_cache.need_refresh:
            models = list(
                await self.get_filtered_model_names(
                    controller=controller,
                    models=None,
                    model_mappings=kwargs["controller_config"].model_mapping,
                )
            )
            file_cache = self.save_cache_data(
                controller,
                data={
                    "models": models,
                    "refresh": kwargs["refresh"],
                },
            )

        self.logger.debug(
            "%s list models: %s", controller.controller_uuid, file_cache.data["models"]
        )
        return file_cache.context

    def save_cache_data(self, controller: Controller, data: Dict[str, Any]) -> FileCache:
        """Gracefully save cache data to default cache directory."""
        file_cache = FileCache(
            uuid=controller.controller_uuid,
            name=controller.controller_name,
            data=data,
            timestamp=time(),
        )
        fname = f"{self.name}_{controller.controller_uuid}"
        error_message_template = "%s list models failed to save cache: %s."
        try:
            file_cache.commit(fname)
            self.logger.debug(
                "%s list models: save result to cache `%s`", controller.controller_uuid, str(fname)
            )
        except JujuSpellError as error:
            self.logger.warning(error_message_template, controller.controller_uuid, str(error))
        return file_cache

    def load_cache_data(self, controller: Controller) -> Optional[FileCache]:
        """Gracefully load cache data from default cache directory."""
        file_cache = None
        fname = f"{self.name}_{controller.controller_uuid}"
        error_message_template = "%s list models failed to load cache: %s."
        try:
            file_cache = FileCache.connect(fname)
            file_cache.data["refresh"] = False
            self.logger.debug(
                "%s list models: load result from cache `%s`",
                controller.controller_uuid,
                str(fname),
            )
        except JujuSpellError as error:
            self.logger.warning(error_message_template, controller.controller_uuid, str(error))
        return file_cache
