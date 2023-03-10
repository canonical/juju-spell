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
"""Revoke commands."""
from typing import Any, Optional

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

__all__ = ["RevokeCommand", "RevokeModelCommand"]


class RevokeCommand(BaseJujuCommand):
    """Revoke user permission on controller."""

    async def execute(
        self,
        controller: Controller,
        user: Optional[str] = None,
        acl: Optional[str] = "login",
        **kwargs: Any,
    ) -> bool:
        """Execute."""
        await controller.revoke(username=user, acl=acl)
        return True


class RevokeModelCommand(BaseJujuCommand):
    """Revoke user permission on model."""

    async def execute(
        self,
        controller: Controller,
        user: Optional[str] = None,
        model_uuid: Optional[str] = None,
        acl: Optional[str] = "read",
        **kwargs: Any,
    ) -> bool:
        """Execute."""
        await controller.revoke_model(username=user, model_uuid=model_uuid, acl=acl)
        return True
