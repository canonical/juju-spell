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
from getpass import getpass
from typing import Any

import yaml
from craft_cli import emit
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.add_user import AddUserCommand
from juju_spell.settings import PERSONAL_CONFIG_PATH


class AddUserCMD(JujuWriteCMD):
    """JujuSpell add user command."""

    name = "add-user"
    help_msg = "add juju user to remote controller"
    overview = textwrap.dedent(
        """
        The command will create user on controller with random_password or given
        password and print the yaml config to stdout.

        Example:
        $ juju-spell add-user --user newuser
        Continue on cmd: add-user parsed_args: Namespace(no_confirm=False,
        run_type='serial', filter='', models=None, user='newuser', display_name=None,
        password=None)[Y/n]: y
        Password(If empty will use random password):
        Please put user information to personal
        config(/home/ubuntu/.local/share/juju-spell/config.personal.yaml):

        controllers:
        - uuid: e9fe93a8-b705-4067-8f30-6eec183eeb4f
          name: controller1
          user: newuser
          password: H4A-GZLxn5Xr4g5aZ9aeymtN7L9kNxfmoTEJd_EB
        """
    )

    command = AddUserCommand

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser=parser)
        parser.add_argument(
            "--user",
            type=str,
            help="username to create",
            required=True,
        )
        parser.add_argument(
            "--display_name",
            type=str,
            help=("display_name to create. If display_name is None then it will be set as user"),
            required=False,
        )
        parser.add_argument(
            "-p",
            dest="password",
            nargs="?",
            required=False,
            help=argparse.SUPPRESS,
        )

    def before(self, parsed_args: argparse.Namespace) -> None:
        """Run before execution."""
        super().before(parsed_args=parsed_args)
        parsed_args.password = getpass("Password(If empty will use random password): ")
        if not parsed_args.display_name:
            parsed_args.display_name = parsed_args.user

    @staticmethod
    def format_output(retval: Any) -> str:
        """Pretty formatter for output.

        Notes:
            - The first element of retval, which is a list, is a list of controllers'
            output. The example:

            retval =
            [
                {
                    "context": {
                        ...
                    },
                    "success": true,
                    "output": {
                        "uuid": "e9fe93a8-b705-4067-8f30-6eec183eeb4f",
                        "user": "Frodo",
                        "display_name": "Frodo",
                        "password": "dRhCziem0IcbV3OEcqWG5LCDXItP69WokeDDzgJ6"
                    },
                   "error": null
                },
            ]
        """
        emit.debug(f"formatting `{retval}`")

        controllers = []

        for controller_output in retval:
            output = {
                "uuid": controller_output["context"]["uuid"],
                "name": controller_output["context"]["name"],
            }
            if controller_output["output"] is not None:
                output["user"] = controller_output["output"]["user"]
                output["password"] = controller_output["output"]["password"]
            else:
                output["error"] = str(controller_output["error"])

            controllers.append(output)

        yaml_str = yaml.dump(
            {"controllers": controllers},
            default_flow_style=False,
            allow_unicode=True,
            encoding=None,
            sort_keys=False,
        )
        return (
            f"Please put user information to personal config({PERSONAL_CONFIG_PATH}):"
            f"{os.linesep}{os.linesep}{yaml_str}{os.linesep}"
        )
