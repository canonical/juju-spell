import dataclasses
import json
import re
from typing import Dict, List

from juju.action import Action
from juju.controller import Controller
from juju.model import Model
from juju.unit import Unit

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.commands.status import StatusCommand

__all__ = ["UpdatePackages"]

UPDATE_TEMPLATE = (
    "sudo apt-get update ; sudo apt-get "
    "--option=Dpkg::Options::=--force-confold --option=Dpkg::Options::=--force-confdef "
    "{install} --upgrade -y {packages}"
)

TIMEOUT_TO_RUN_COMMAND_SECONDS = 600


@dataclasses.dataclass
class UnitUpdate:
    unit: str
    packages: Dict[str, str]


@dataclasses.dataclass
class Update:
    units: List[UnitUpdate]
    application: str


@dataclasses.dataclass
class Container:
    updates: List[Update]


class UpdatePackages(BaseJujuCommand):
    async def execute(self, controller: Controller, **kwargs):
        default_model = kwargs["controller_config"].model_mapping["default"]
        updates = kwargs["patch"]
        juju_status = await self.get_juju_status(controller, default_model)
        apps_to_update = self.get_apps_to_update(juju_status, updates)
        update_commands = self.get_update_commands(apps_to_update)

        update_result: List[Update] = []
        for update, app, units, command in update_commands:
            single_app: Update = Update(application=app, units=[])
            for unit in units:
                _, result = await self.run_on_unit(
                    controller=controller,
                    model=default_model,
                    command=command,
                    unit=unit,
                )
                unit_update: UnitUpdate = self.parse_result(unit, result)
                single_app.units.append(unit_update)
            update_result.append(single_app)

        mylist = [dataclasses.asdict(result) for result in update_result]
        print(json.dumps(mylist))
        return Container(updates=update_result)

    def parse_result(self, unit: str, result: str):
        lines = result.splitlines()
        unit_update: UnitUpdate = UnitUpdate(unit=unit, packages={})
        for line in lines:
            if line.startswith("Inst") or line.startswith("Unpacking"):
                app_name, _, to_version = self.parse_line(line)
                unit_update.packages[app_name] = to_version
        return unit_update

    def parse_line(self, line: str):
        # Inst libdrm2 [2.4.110-1ubuntu1] (2.4.113-2~ubuntu0.22.04.1
        # Ubuntu:22.04/jammy-updates [amd64])
        if line.startswith("Inst"):
            _, name, from_version, to_version, *others = line.split(" ")
        elif line.startswith("Unpacking"):
            # Unpacking software-properties-common (0.99.9.11) over (0.99.9.10)
            _, name, from_version, _, to_version, *others = line.split(" ")
        return name, from_version.strip("()[]"), to_version.strip("()[]")

    async def dry_run(self):
        ...

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
        for update, app, units in apps_to_update:
            if update.get("dist-upgrade", "false").casefold() == "true".casefold():
                update_command = UPDATE_TEMPLATE.format(
                    install="dist-upgrade", packages=""
                )
            else:
                package_list = self.get_update_package_list(update)
                update_command = UPDATE_TEMPLATE.format(
                    install="install", packages=package_list
                )
            update_commands.append((update, app, list(units), update_command))
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
                    apps_to_update.append((update, app, list(app_status.units.keys())))
        return apps_to_update

    async def get_juju_status(self, controller, default_model):
        juju_status_map = await StatusCommand.execute(
            self, controller=controller, models=[default_model]
        )
        juju_status = juju_status_map[default_model]
        return juju_status
