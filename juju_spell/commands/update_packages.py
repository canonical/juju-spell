"""Command to update packages on units."""
import copy
import dataclasses
import re
from typing import Any, Dict, List, Optional, Tuple

from juju.action import Action
from juju.controller import Controller
from juju.model import Model

from juju_spell.commands.base import BaseJujuCommand, Result

__all__ = ["UpdatePackagesCommand"]

UPDATE_TEMPLATE = (
    "sudo apt-get update ; sudo apt-get "
    "--option=Dpkg::Options::=--force-confold --option=Dpkg::Options::=--force-confdef "
    "{install} --upgrade -y {packages} "
)

TIMEOUT_TO_RUN_COMMAND_SECONDS = 600


@dataclasses.dataclass
class PackageUpdateResult:
    """Package update result."""

    package: str
    from_version: str
    to_version: str


@dataclasses.dataclass
class UnitUpdateResult:
    """Juju unit update result."""

    unit: str
    command: str
    packages: List[PackageUpdateResult]
    raw_output: Optional[str] = ""
    success: bool = False


@dataclasses.dataclass
class UpdateResult:
    """Update result for all units for application."""

    units: List[UnitUpdateResult]
    application: str


@dataclasses.dataclass
class PackageToUpdate:
    """Package to update and version."""

    package: str
    version: str


@dataclasses.dataclass
class Application:
    """Application to update and its packages."""

    name_expr: str
    dist_upgrade: bool
    packages_to_update: List[PackageToUpdate]
    results: List[UpdateResult]  # output


@dataclasses.dataclass
class Updates:
    """Encapsulating update class."""

    applications: List[Application]


class UpdatePackagesCommand(BaseJujuCommand):
    """Update packages command."""

    async def execute(
        self,
        controller: Controller,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover
        """Run update."""
        self.logger.info("Running execute on controller %s", controller.controller_name)
        return await self.make_updates(
            controller=controller,
            models=kwargs["models"],
            model_mapping=kwargs["controller_config"].model_mapping,
            updates=kwargs["patch"],
            dry_run=False,
        )

    async def dry_run(
        self,
        controller: Controller,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover
        """Run dry-run."""
        self.logger.info("Running dry-run on controller %s", controller.controller_name)
        return await self.make_updates(
            controller=controller,
            models=kwargs["models"],
            model_mapping=kwargs["controller_config"].model_mapping,
            updates=kwargs["patch"],
            dry_run=True,
        )

    # pylint: disable-next=too-many-arguments
    async def make_updates(
        self,
        controller: Controller,
        models: Optional[List[str]],
        dry_run: bool,
        model_mapping: Dict[str, List[str]],
        updates: Updates,
    ) -> Optional[Result]:
        """Run the updates or dry-run."""
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

    async def run_updates_on_model(self, model: Model, updates: Updates) -> None:
        """Run updates on model.

        Runs the command on unit and parses the result and assigns it to each unit.
        """
        for app in updates.applications:
            for result in app.results:
                for unit in result.units:
                    juju_unit = model.units[unit.unit]
                    self.logger.info(
                        "updating model:%s unit:%s with command:%s",
                        model.info.name,
                        unit.unit,
                        unit.command,
                    )
                    action: Action = await juju_unit.run(
                        command=unit.command, timeout=TIMEOUT_TO_RUN_COMMAND_SECONDS
                    )
                    stdout = action.data["results"]["Stdout"]
                    updated_packages = self.parse_result(stdout)
                    unit.packages = updated_packages
                    self.set_success_flags(unit, app.packages_to_update)
                    unit.raw_output = stdout

    def parse_result(self, result: str) -> List[PackageUpdateResult]:
        """Parse result.

        Parses the result and creates PackageUpdateResult structure.
        """
        lines = result.splitlines()
        packages: List[PackageUpdateResult] = []
        for line in lines:
            from_version, name, to_version = self.parse_line(line)
            if from_version != "" and to_version != "" and name != "":
                packages.append(
                    PackageUpdateResult(
                        package=name, from_version=from_version, to_version=to_version
                    )
                )

        return packages

    def parse_line(self, line: str) -> Tuple[str, str, str]:
        """Parse the line and return (from_version, name, to_version) tuple."""
        # pylint: disable-next=line-too-long
        # Inst libdrm2 [2.4.110-1ubuntu1] (2.4.113-2~ubuntu0.22.04.1 Ubuntu:22.04/jammy-updates [amd64]) # noqa
        to_version = ""
        from_version = ""
        name = ""
        if line.startswith("Inst "):
            _, name, from_version, to_version, *_ = line.split(" ")

        # Unpacking software-properties-common (0.99.9.11) over (0.99.9.10)
        elif line.startswith("Unpacking"):
            _, name, to_version, _, from_version, *_ = line.split(" ")
        to_version = to_version.strip("()[]")
        from_version = from_version.strip("()[]")
        name = name.strip(" ")
        return from_version, name, to_version

    def get_update_command(self, app: Application, dry_run: bool) -> str:
        """Generate command according to flags."""
        template = UPDATE_TEMPLATE + ("--dry-run" if dry_run else "")
        if app.dist_upgrade:
            return template.format(install="dist-upgrade", packages="")

        app_list = [a.package for a in app.packages_to_update]
        package_list = " ".join(app_list)
        return template.format(install="install", packages=package_list)

    def set_apps_to_update(self, model: Model, updates: Updates, dry_run: bool) -> None:
        """Set units to applications.

        Finds the matching applications and set the units of these applications as a
        List[UpdateResult] to application.
        """
        self.logger.info("Finding applications to update on model:%s", model.info.name)
        for update in updates.applications:
            command = self.get_update_command(app=update, dry_run=dry_run)
            for app, app_status in model.applications.items():
                if re.match(update.name_expr, app):
                    self.logger.info(
                        "model:%s application:%s units:%s will be updated",
                        model.info.name,
                        app,
                        [u.name for u in app_status.units],
                    )
                    unit_updates = [
                        UnitUpdateResult(unit=u.name, command=command, packages=[])
                        for u in app_status.units
                    ]
                    update.results.append(UpdateResult(application=app, units=unit_updates))

    def set_success_flags(self, unit: UnitUpdateResult, expected: List[PackageToUpdate]) -> None:
        """Set success flag for each unit."""
        expected_set = set((e.version, e.package) for e in expected)
        real_set = set((p.to_version, p.package) for p in unit.packages)

        res = expected_set.intersection(real_set)
        unit.success = res == expected_set
