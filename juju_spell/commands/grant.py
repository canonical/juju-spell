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
"""Command to grant permission for user."""
from typing import Any, List, Optional

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

__all__ = ["GrantCommand", "ACL_CHOICES"]

CONTROLLER_ACL_CHOICES = ["login", "add-model", "superuser"]
MODEL_ACL_CHOICES = ["read", "write", "admin"]

ACL_CHOICES = CONTROLLER_ACL_CHOICES + MODEL_ACL_CHOICES


class GrantCommand(BaseJujuCommand):
    """Grant permission for user."""

    async def execute(
        self,
        controller: Controller,
        *args: Any,
        models: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> bool:
        """Execute."""
        acl = kwargs["acl"]
        controller_acl: str
        model_acl: str
        if acl in CONTROLLER_ACL_CHOICES:
            controller_acl = acl
        else:
            controller_acl = "login"

        if acl in MODEL_ACL_CHOICES:
            model_acl = acl
        elif acl == "superuser":
            model_acl = "admin"
        else:
            model_acl = "read"

        result: bool = await controller.grant(username=kwargs["user"], acl=controller_acl)
        if not result:
            return result

        async for _, model in self.get_filtered_models(
            controller=controller,
            models=models,
            model_mappings=kwargs["controller_config"].model_mapping,
        ):
            grant_model_result: bool = await controller.grant_model(
                username=kwargs["user"],
                model_uuid=model.uuid,
                acl=model_acl,
            )
            if not grant_model_result:
                return grant_model_result
        return True
