import json
import re

from juju.action import Action
from juju.controller import Controller
from juju.model import Model
from juju.unit import Unit

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.commands.status import StatusCommand

__all__ = ["UpdatePackages"]

UPDATE_TEMPLATE = (
    "sudo apt-get update ; sudo apt-get    "
    " --option=Dpkg::Options::=--force-confold--option=Dpkg::Options::=--force-confdef "
    "    install --upgrade -y {}"
)

TIMEOUT_TO_RUN_COMMAND_SECONDS = 600


class UpdatePackages(BaseJujuCommand):
    async def execute(self, controller: Controller, **kwargs):
        default_model = kwargs["controller_config"].model_mapping["default"]
        updates = self.get_patch_config(kwargs)
        juju_status = await self.get_juju_status(controller, default_model)
        apps_to_update = self.get_apps_to_update(juju_status, updates)
        update_commands = self.get_update_commands(apps_to_update)

        for update, units, command in update_commands:
            for unit in units:
                _, result = await self.run_on_unit(
                    controller=controller,
                    model=default_model,
                    command=command,
                    unit=unit,
                )
                print(result)
            # TODO: output = juju ssh units/1 command
            # TODO: parse output as (package, from, to)
            # TODO: check if update target is reached
            ...

        print(update_commands)
        return result

    async def run_on_unit(
        self, controller: Controller, model: str, unit: str, command: str
    ) -> str:
        """Run shell command in unit."""
        mdl: Model = await controller.get_model(model)
        unit_to_run_on: Unit = mdl.units[unit]
        action: Action = await unit_to_run_on.run(
            command=command, timeout=TIMEOUT_TO_RUN_COMMAND_SECONDS
        )
        return action.data["results"]["Code"], action.data["results"]["Stdout"]

    def get_update_commands(self, apps_to_update):
        update_commands = []
        for update, units in apps_to_update:
            if (
                update["dist-upgrade"]
                and update["dist-upgrade"].casefold() == "true".casefold()
            ):
                update_command = UPDATE_TEMPLATE.format("")
            else:
                package_list = self.get_update_package_list(update)
                update_command = UPDATE_TEMPLATE.format(package_list)
            update_commands.append((update, list(units), update_command))
        return update_commands

    def get_update_package_list(self, update):
        app_list = []
        for app in update["packages-to-update"]:
            app_list.append(app["app"])
        package_list = " ".join(app_list)
        return package_list

    def get_apps_to_update(self, juju_status, updates):
        apps_to_update = []
        for update in updates:
            for app, app_status in juju_status.applications.items():
                if re.match(update["application"], app):
                    apps_to_update.append((update, app_status.units.keys()))
        return apps_to_update

    async def get_juju_status(self, controller, default_model):
        juju_status_map = await StatusCommand.execute(
            self, controller=controller, models=[default_model]
        )
        juju_status = juju_status_map[default_model]
        return juju_status

    def get_patch_config(self, kwargs):
        update_file = kwargs["patch"]
        update_config = update_file.read()
        updates = json.loads(update_config)["updates"]
        return updates
