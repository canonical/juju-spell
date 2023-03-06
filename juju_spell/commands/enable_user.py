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
"""Command to enable users."""
from typing import Any

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.exceptions import JujuSpellError

__all__ = ["EnableUserCommand"]


class EnableUserCommand(BaseJujuCommand):
    """Enable user."""

    async def execute(self, controller: Controller, *args: Any, **kwargs: Any) -> bool:
        """Execute."""
        result: bool = await controller.enable_user(username=kwargs["user"])
        if not result:
            raise JujuSpellError(
                f"Enable user {kwargs['user']} on controller {controller.uuid} fail"
            )
        return result
