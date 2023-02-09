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
import os
import textwrap
from typing import Any

import yaml
from craft_cli import emit
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.update_packages import UpdatePackages
from juju_spell.settings import PERSONAL_CONFIG_PATH


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

    @staticmethod
    def format_output(retval: Any) -> str:
        """Pretty formatter for output.

        Notes:
            - The first element of retval, which is a list, is a list of controllers'
            output. The example:

            retval =
                [
                  {
                    "output": {
                      "updates": [
                        {
                          "unit": "nova-common",
                          "packages": [
                            {
                              "app": "nova-common",
                              "version": "2:21.2.4-0ubuntu2.1",
                              "success": "true"
                            },
                            {
                              "app": "python3-nova",
                              "version": "2:21.2.4-0ubuntu2.1",
                              "success": "true"
                            }
                          ]
                        },
                        {
                          "unit": "glance",
                          "packages": [
                            {
                              "app":"glance-common",
                              "version":"2:20.2.0-0ubuntu1.1",
                              "success": "true"
                            },
                            {
                              "app":"python3-glance",
                              "version": "2:20.2.0-0ubuntu1.1",
                              "success": "true"
                            }
                          ]
                        }
                      ]
                    },
                    "context": {
                      "name": "controller_config.name",
                      "customer": "controller_config.customer"
                    }
                  }
                ]
        """
        emit.debug(f"formatting `{retval}`")

        output = {"controllers": []}
        for controller_output in retval[0]:
            output["controllers"].append(controller_output["output"])

        yaml_str = yaml.dump(
            output, default_flow_style=False, allow_unicode=True, encoding=None
        )
        return (
            f"Please put user information to personal config({PERSONAL_CONFIG_PATH}):"
            f"{os.linesep}{os.linesep}{yaml_str}{os.linesep}"
        )
