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
"""CLI command to grant user privileges."""
import textwrap

from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.grant import ACL_CHOICES, GrantCommand


class GrantCMD(JujuWriteCMD):
    """Grant command."""

    name = "grant"
    help_msg = "add juju user to remote controller"
    overview = textwrap.dedent(
        """
        The command will set access level of user to controller.

        Example:
        $ juju-spell grant --user newuser --acl superuser
        Continue on cmd: grant parsed_args: Namespace(no_confirm=False,
        run_type='serial', filter='', models=None, user='newuser',
        acl='superuser')[Y/n]: y
        [
         {
          "context": {
           "uuid": "e9fe93a8-b705-4067-8f30-6eec183eeb4f",
           "name": "controller1",
           "customer": "Gandalf"
          },
          "success": true,
          "output": true,
          "error": null
         }
        ]
        """
    )

    command = GrantCommand

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser=parser)
        parser.add_argument(
            "--user",
            type=str,
            help="username to grant",
            required=True,
        )
        parser.add_argument(
            "--acl",
            type=str,
            choices=ACL_CHOICES,
            help=f"Access control. e.g., {','.join(ACL_CHOICES)}.",
            default=False,
            required=True,
        )
