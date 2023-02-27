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
from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

__all__ = ["GrantCommand", "ACL_CHOICES"]

ACL_CHOICES = ["login", "add-model", "superuser"]


class GrantCommand(BaseJujuCommand):
    """Grant permission for user."""

    async def execute(self, controller: Controller, **kwargs) -> bool:
        """Execute."""
        result: bool = await controller.grant(username=kwargs["user"], acl=kwargs["acl"])
        return result
