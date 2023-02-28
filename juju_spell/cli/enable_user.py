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
"""CLI command to enable user."""
import textwrap

from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.enable_user import EnableUserCommand


class EnableUserCMD(JujuWriteCMD):
    """Enable user command."""

    name = "enable-user"
    help_msg = "add juju user to remote controller"
    overview = textwrap.dedent(
        """
        The command will enable user for controller.

        Example:
        $ juju-spell enable_user --user newuser
        Continue on cmd: enable-user parsed_args: Namespace(dry_run=False,
        no_confirm=False, run_type='serial',filter='', models=None,
        user='newuser-abc')[Y/n]: Y
        [
         {
          "context": {
           "uuid": "e9fe93a8-b705-4067-8f30-6eec183eeb4f",
           "name": "controller1",
           "customer": "Gandalf"
          },
          "success": true,
          "output": {
           "results": [
            {
             "error": null,
             "unknown_fields": {}
            }
           ],
           "unknown_fields": {}
          },
          "error": null
         },
        ]
        """
    )

    command = EnableUserCommand

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser=parser)
        parser.add_argument(
            "--user",
            type=str,
            help="username to enable",
            required=True,
        )
