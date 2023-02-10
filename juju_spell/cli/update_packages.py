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
import argparse
import textwrap

from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.update_packages import UpdatePackages


class UpdatePackages(JujuWriteCMD):
    """JujuSpell patch cve command."""

    name = "update-packages"
    help_msg = "patch cve template command"
    overview = textwrap.dedent(
        """
        This command will patch the cve by updating certain components.

        {
          "updates": [
            {
              "application": "^.*nova-compute.*$",
              "dist-upgrade": "true",
              "packages-to-update": [
                {
                  "app": "nova-common",
                  "version": "2:21.2.4-0ubuntu2.1"
                },
                {
                  "app":"python3-nova",
                  "version": "2:21.2.4-0ubuntu2.1"
                }
              ]
            },
            {
              "application": "^.*nova-cloud-controller.*$",
              "packages-to-update": [
                {
                  "app": "nova-common",
                  "version": "2:21.2.4-0ubuntu2.1"
                },
                {
                  "app": "python3-nova",
                  "version": "2:21.2.4-0ubuntu2.1"
                }
              ]
            },
            {
              "application": "^.*glance.*$",
              "packages-to-update": [
                {
                  "app":"glance-common",
                  "version":"2:20.2.0-0ubuntu1.1"
                },
                {
                  "app":"python3-glance",
                  "version": "2:20.2.0-0ubuntu1.1"
                }
              ]
            },
            {
              "application": "^.*cinder.*$",
              "packages-to-update": [
                {
                  "app":"cinder-common",
                  "version": "2:16.4.2-0ubuntu2.1"
                },
                {
                  "app":"python3-cinder",
                  "version":"2:16.4.2-0ubuntu2.1"
                }
              ]
            }
          ]
        }
        Example:
        $ juju_spell update-packages --patch patchfile.json

        """
    )

    command = UpdatePackages

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser=parser)
        parser.add_argument(
            "--patch",
            type=argparse.FileType("r"),
            help="patch file",
            required=True,
        )

    def dry_run(self, parsed_args: argparse.Namespace) -> None:
        ...
