import copy
import dataclasses
import re
from typing import Dict, List, Optional

from juju.action import Action
from juju.controller import Controller
from juju.model import Model

from juju_spell.commands.base import BaseJujuCommand, Result

__all__ = ["UpdatePackages"]

UPDATE_TEMPLATE = (
    "sudo apt-get update ; sudo apt-get "
    "--option=Dpkg::Options::=--force-confold --option=Dpkg::Options::=--force-confdef "
    "{install} --upgrade -y {packages} "
)

TIMEOUT_TO_RUN_COMMAND_SECONDS = 600


@dataclasses.dataclass
class PackageUpdateResult:
    package: str
    from_version: str
    to_version: str


@dataclasses.dataclass
class UnitUpdateResult:
    unit: str
    command: str
    raw_output: Optional[str] = ""
    packages: Optional[List[PackageUpdateResult]] = None
    success: bool = False


@dataclasses.dataclass
class UpdateResult:
    units: List[UnitUpdateResult]
    application: str


@dataclasses.dataclass
class PackageToUpdate:
    package: str
    version: str


@dataclasses.dataclass
class Application:
    name_expr: str
    dist_upgrade: bool
    packages_to_update: List[PackageToUpdate]
    results: List[UpdateResult]  # output


@dataclasses.dataclass
class Updates:
    applications: List[Application]


class UpdatePackages(BaseJujuCommand):
    async def execute(
        self, controller: Controller, models: Optional[List[str]] = None, **kwargs
    ) -> Optional[Result]:
        """Run update."""
        return await self.make_updates(
            controller=controller,
            models=models,
            model_mapping=kwargs["controller_config"].model_mapping,
            updates=kwargs["patch"],
            dry_run=False,
        )

    async def dry_run(
        self, controller: Controller, models: Optional[List[str]] = None, **kwargs
    ) -> Optional[Result]:
        """Run update with --dry-run flag."""
        return await self.make_updates(
            controller=controller,
            models=models,
            model_mapping=kwargs["controller_config"].model_mapping,
            updates=kwargs["patch"],
            dry_run=True,
        )

    async def make_updates(
        self,
        controller: Controller,
        models: Optional[List[str]],
        dry_run: bool,
        model_mapping: Dict[str, List[str]],
        updates: Updates,
    ) -> Optional[Result]:
        output = {}
        async for name, model in self.get_filtered_models(
            controller=controller,
            model_mappings=model_mapping,
            models=models,
        ):
            model_result: Updates = copy.deepcopy(updates)
            self.set_apps_to_update(model, model_result, dry_run=dry_run)
            await self.run_updates_on_model(model, model_result)

            output[name] = model_result
        return Result(output=output, success=True, error=None)

    async def run_updates_on_model(self, model: Model, updates: Updates):
        """Run updates on model.

        Runs the command on unit and parses the result and assigns it to each unit.
        """
        for app in updates.applications:
            for result in app.results:
                for unit in result.units:
                    juju_unit = model.units[unit.unit]
                    action: Action = await juju_unit.run(
                        command=unit.command, timeout=TIMEOUT_TO_RUN_COMMAND_SECONDS
                    )
                    result = action.data["results"]["Stdout"]
                    updated_packages = self.parse_result(result)
                    unit.packages = updated_packages
                    self.set_success_flags(unit, app.packages_to_update)
                    unit.raw_output = result

    def parse_result(self, result: str):
        """Parse result.

        Parses the result and creates PackageUpdateResult structure.
        """
        lines = result.splitlines()
        packages: List[PackageUpdateResult] = []
        for line in lines:
            # Inst libdrm2 [2.4.110-1ubuntu1] (2.4.113-2~ubuntu0.22.04.1 Ubuntu:22.04/jammy-updates [amd64]) # noqa
            to_version = ""
            from_version = ""
            name = ""
            if line.startswith("Inst "):
                _, name, from_version, to_version, *others = line.split(" ")

            # Unpacking software-properties-common (0.99.9.11) over (0.99.9.10)
            elif line.startswith("Unpacking"):
                _, name, to_version, _, from_version, *others = line.split(" ")

            to_version = to_version.strip("()[]")
            from_version = from_version.strip("()[]")
            name = name.strip(" ")
            if from_version != "" and to_version != "" and name != "":
                packages.append(
                    PackageUpdateResult(
                        package=name, from_version=from_version, to_version=to_version
                    )
                )

        return packages

    def get_update_command(self, app: Application, dry_run: bool):
        """Generate command according to flags."""
        template = UPDATE_TEMPLATE + ("--dry-run" if dry_run else "")
        if app.dist_upgrade:
            return template.format(install="dist-upgrade", packages="")
        else:
            app_list = [a.package for a in app.packages_to_update]
            package_list = " ".join(app_list)
            return template.format(install="install", packages=package_list)

    def set_apps_to_update(self, model: Model, updates: Updates, dry_run: bool):
        """Set units to applications.

        Finds the matching applications and set the units of these applications as a
        List[UpdateResult] to application.
        """
        for update in updates.applications:
            command = self.get_update_command(app=update, dry_run=dry_run)
            for app, app_status in model.applications.items():
                if re.match(update.name_expr, app):
                    unit_updates = [
                        UnitUpdateResult(unit=u.name, command=command)
                        for u in app_status.units
                    ]
                    update.results.append(
                        UpdateResult(application=app, units=unit_updates)
                    )

    def set_success_flags(
        self, unit: UnitUpdateResult, expected: List[PackageToUpdate]
    ):
        """Set success flag for each unit."""
        expected_set = set([(e.version, e.package) for e in expected])
        real_set = [(p.to_version, p.package) for p in unit.packages]

        res = expected_set.intersection(real_set)
        unit.success = res == expected_set
