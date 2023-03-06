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
"""Command to remove users."""
from typing import Any, List, Optional, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand, Result
from juju_spell.commands.enable_user import DisableUserCommand
from juju_spell.commands.revoke import RevokeCommand, RevokeModelCommand

__all__ = ["RemoveUserCommand"]


class RemoveUserCommand(BaseJujuCommand):
    """Remove user command."""

    async def execute(
        self,
        controller: Controller,
        *args: Any,
        models: Optional[List[str]] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[bool, Result]:
        """Execute."""
        # Revoke
        revoke_cmd = RevokeCommand()
        revoke_result = await revoke_cmd.run(controller=controller, user=user, acl="login")
        if not revoke_result.success:
            return revoke_result

        # Revoke model
        revoke_model_cmd = RevokeModelCommand()
        async for _, model in self.get_filtered_models(
            controller=controller,
            models=models,
            model_mappings=kwargs["controller_config"].model_mapping,
        ):
            revoke_model_result = await revoke_model_cmd.run(
                controller=controller, user=user, model_uuid=model.uuid, acl="read"
            )
            if not revoke_model_result.success:
                return revoke_model_result

        # Disable
        disable_cmd = DisableUserCommand()
        disable_result = await disable_cmd.run(controller=controller, user=user)
        if not disable_result.success:
            return disable_result

        self.logger.info("%s user `%s` was successfully removed", controller.controller_uuid, user)
        return True
