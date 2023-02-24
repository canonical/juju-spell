# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""JujuSpell juju add user command."""
import logging
import textwrap
from typing import List

import yaml
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.update_packages import (
    Application,
    PackageToUpdate,
    UpdatePackages,
    Updates,
)
from juju_spell.exceptions import JujuSpellError

logger = logging.getLogger(__name__)


class UpdatePackages(JujuWriteCMD):
    """JujuSpell patch cve command."""

    name = "update-packages"
    help_msg = "patch cve template command"
    overview = textwrap.dedent(
        """
        This command will patch the cve by updating certain components.

        ---
        applications:
        - application: "^.*ubuntu.*$"
          dist_upgrade: True
          packages_to_update:
          - app: nova-common
            version: 2:21.2.4-0ubuntu2.1
          - app: python3-nova
            version: 2:21.2.4-0ubuntu2.1
        - application: "^.*nova-cloud-controller.*$"
          dist_upgrade: False
          packages_to_update:
          - app: nova-common
            version: 2:21.2.4-0ubuntu2.1
          - app: python3-nova
            version: 2:21.2.4-0ubuntu2.1

        Example:
        $ juju_spell update-packages --patch patchfile.yaml

        """
    )

    command = UpdatePackages

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser=parser)
        parser.add_argument(
            "--patch",
            type=get_patch_config,
            help="patch file",
            required=True,
        )


def load_patch_file(path: str):
    """Load patch file.

    raises: IsADirectoryError if path is directory
    raises: FileNotFoundError -> JujuSpellError if fies does not exist
    raises: PermissionError -> JujuSpellError if user has no permission to path
    """
    try:
        with open(path, "r") as file:
            source = yaml.safe_load(file)
            logger.info("load config file from %s path", path)
            return source
    except FileNotFoundError as error:
        logger.error("config file `%s` does not exists", path)
        raise JujuSpellError(f"config file {path} does not exist") from error
    except PermissionError as error:
        logger.error("not enough permission for configuration file `%s`", path)
        raise JujuSpellError(f"permission denied to read config file {path}") from error


def get_patch_config(file_path: str):
    patch = load_patch_file(file_path)
    applications: List[Application] = []
    errors = []
    for app in patch["applications"]:
        packages_to_update: List[PackageToUpdate] = []
        for package in app.get("packages_to_update", []):
            package_to_update = PackageToUpdate(
                package=package["app"], version=package.get("version", None)
            )
            packages_to_update.append(package_to_update)

        dist_upgrade = app.get("dist_upgrade", False)
        if not isinstance(dist_upgrade, bool):
            errors.append(
                f"application['{app['application']}'].dist_upgrade should be bool"
            )
        applications.append(
            Application(
                name_expr=app["application"],
                dist_upgrade=dist_upgrade,
                results=[],
                packages_to_update=packages_to_update,
            )
        )

    if len(errors) > 0:
        raise JujuSpellError("errors in input file:\n" + "\n".join(errors))

    return Updates(applications=applications)
