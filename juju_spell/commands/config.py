"""Config command for juju-spell."""
import dataclasses
import logging
from typing import Any, Dict, List

from juju.application import Application
from juju.controller import Controller
from juju.model import Model

from juju_spell.commands.base import BaseJujuCommand

logger = logging.getLogger()


@dataclasses.dataclass
class ApplicationConfig:
    """Dataclass for holding juju application config."""

    application: str
    config: Dict[str, str]


class ConfigCommand(BaseJujuCommand):
    """Command to configure juju applications."""

    async def execute(self, controller: Controller, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Configure juju applications."""
        output: Dict[str, Any] = {}
        async for name, model in self.get_filtered_models(
            controller=controller,
            models=kwargs.get("models", None),
            model_mappings=kwargs["controller_config"].model_mapping,
        ):
            config = await apply_configuration(kwargs, model)
            logger.info("%s model %s", controller.controller_uuid, name)
            output[name] = config

        return output


async def apply_configuration(kwargs: Dict[str, Any], model: Model) -> Dict[str, Any]:
    """Get the parameter and apply config on model."""
    config: Dict[str, Any] = {}
    application: str = kwargs.get("config_app", None)
    updates: List[ApplicationConfig] = kwargs.get("config_file", None)
    single_property: str = kwargs.get("config_get", None)
    properties: Dict[str, str] = kwargs.get("config_set", None)

    if application:
        juju_app: Application = model.applications.get(application)
        if not juju_app:
            logger.warning("Unable to find application %s", application)
            return config

        if properties:
            await juju_app.set_config(properties)

        all_config_of_app = await juju_app.get_config()
        if single_property:
            config[application] = {single_property: all_config_of_app[single_property]}
        else:
            config[application] = all_config_of_app

    elif updates:
        config = await apply_file_config(model, updates)
    return config


async def apply_file_config(model: Model, updates: List[ApplicationConfig]) -> dict:
    """Apply file configuration to (multiple) juju applications."""
    config = {}
    for update in updates:
        juju_app: Application = model.applications.get(update.application)
        if not juju_app:
            continue

        await juju_app.set_config(update.config)
        config.update({update.application: await juju_app.get_config()})
    return config
