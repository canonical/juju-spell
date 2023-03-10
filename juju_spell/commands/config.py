"""Config command for juju-spell."""
import dataclasses
import logging
from typing import Any, Dict, List, Union

from craft_cli import emit
from juju.application import Application
from juju.controller import Controller
from juju.model import Model
from websockets.exceptions import InvalidStatusCode

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
        try:
            async for name, model in self.get_filtered_models(
                controller=controller,
                models=kwargs.get("models", None),
                model_mappings=kwargs["controller_config"].model_mapping,
            ):
                emit.message(f"{controller.controller_uuid} model:{name} processing")
                config = await apply_configuration(kwargs, model)
                output[name] = config
        except InvalidStatusCode:
            emit.message(f"{controller.controller_uuid} unable to connect model")

        return output


async def apply_configuration(kwargs: Dict[str, Any], model: Model) -> Dict[str, Any]:
    """Get the parameter and apply config on model."""
    config: Dict[str, Any] = {}
    application: str = kwargs.get("config-app", None)
    updates: List[ApplicationConfig] = kwargs.get("config_file", None)
    single_property: str = kwargs.get("config-get", None)
    properties: Dict[str, str] = kwargs.get("config_set", None)

    if updates:
        config = await apply_file_config(model, updates)
    elif application:
        juju_app: Application = model.applications.get(application)
        if not juju_app:
            emit.message(f"model:{model.info.name} unable to find application:{application}")
            return config

        keys: List[str] = []
        if properties:
            await juju_app.set_config(properties)
            keys = list(properties.keys())

        all_config_of_app = await juju_app.get_config()
        if single_property:
            config[application] = values_only(all_config_of_app, single_property)
        else:
            config[application] = values_only(all_config_of_app, *keys)

    return config


def values_only(
    all_config_of_app: Dict[str, Any], *properties: Union[str, None]
) -> Dict[str, str]:
    """Convert juju config output to cleaner.

    all_config_of_app = {
        "dns-ha": {
          "default": false,
          "description": "Use DNS HA with MAAS 2.0. Note if this is set do not set vip",
          "source": "default",
          "type": "boolean",
          "value": false
         },
         "xxxx": {
          "default": false,
          "description": "Use DNS HA with MAAS 2.0. Note if this is set do",
          "source": "default",
          "type": "boolean",
          "value": false
         }
    }
    properties = [dns-ha]

    to ->
    {
        "dns-ha": false,
    }
    """
    new_values: Dict[str, str] = {}
    for key, value in all_config_of_app.items():
        if not properties or key in properties:
            new_values[key] = value.get("value")

    return new_values


async def apply_file_config(model: Model, updates: List[ApplicationConfig]) -> dict:
    """Apply file configuration to (multiple) juju applications."""
    config = {}
    for update in updates:
        juju_app: Application = model.applications.get(update.application)
        if not juju_app:
            continue

        await juju_app.set_config(update.config)
        all_config = await juju_app.get_config()
        config.update({update.application: values_only(all_config, *update.config.keys())})
    return config
