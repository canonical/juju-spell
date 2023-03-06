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
from typing import Any, Optional

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

__all__ = ["EnableUserCommand", "DisableUserCommand"]


class EnableUserCommand(BaseJujuCommand):
    """Enable user."""

    async def execute(self, controller: Controller, *args: Any, **kwargs: Any) -> None:
        """Execute."""
        await controller.enable_user(username=kwargs["user"])


class DisableUserCommand(BaseJujuCommand):
    """Disable user."""

    async def execute(
        self,
        controller: Controller,
        *args: Any,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Execute."""
        await controller.disable_user(username=user)
