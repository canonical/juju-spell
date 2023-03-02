"""Config command for juju-spell."""
import dataclasses
import logging
from typing import Any, Dict, List

from juju.application import Application
from juju.controller import Controller
from juju.model import Model

from juju_spell.commands.base import BaseJujuCommand

logger = logging.getLogger("eeee")


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
            config = {}
            application: str = kwargs.get("config-app", None)
            updates: List[ApplicationConfig] = kwargs.get("config-file", None)
            single_property: str = kwargs.get("config-get", None)
            properties: Dict[str, str] = kwargs.get("config-set", None)

            if application:
                juju_app: Application = model.applications.get(application)
                if juju_app:
                    config[application] = await apply_config(
                        app=juju_app, properties=properties, single_property=single_property
                    )
            elif updates:
                config = await apply_file_config(model, updates)

            logger.info("%s model %s", controller.controller_uuid, name)
            output[name] = config

        return output


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


async def apply_config(app: Application, properties: Dict[str, str], single_property: str) -> dict:
    """Apply config on a single application."""
    if properties:
        await app.set_config(properties)

    config = await app.get_config()
    if single_property:
        return {single_property: config[single_property]}

    return config
