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
import logging
from typing import Any, List, Optional

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand

__all__ = ["GrantCommand", "ACL_CHOICES"]

CONTROLLER_ACL_CHOICES = ["login", "add-model", "superuser"]
MODEL_ACL_CHOICES = ["read", "write", "admin"]

ACL_CHOICES = CONTROLLER_ACL_CHOICES + MODEL_ACL_CHOICES

logger = logging.getLogger(__name__)


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

        logger.info(
            "Start grant permission %s on controller %s for user %s",
            controller_acl,
            controller.uuid,
            kwargs["user"],
        )
        await controller.grant(username=kwargs["user"], acl=controller_acl)

        async for _, model in self.get_filtered_models(
            controller=controller,
            models=models,
            model_mappings=kwargs["controller_config"].model_mapping,
        ):
            logger.info(
                "Start grant model %s permission %s on controller %s for user %s",
                model.uuid,
                model_acl,
                controller.uuid,
                kwargs["user"],
            )
            await controller.grant_model(
                username=kwargs["user"],
                model_uuid=model.uuid,
                acl=model_acl,
            )
        return True
