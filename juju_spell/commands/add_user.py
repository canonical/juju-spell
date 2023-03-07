"""Command to add users."""
from typing import Any, Dict, Union

from juju.controller import Controller
from juju.errors import JujuError

from juju_spell.commands.base import BaseJujuCommand, Result
from juju_spell.commands.enable_user import EnableUserCommand
from juju_spell.commands.grant import GrantCommand
from juju_spell.utils import random_password

__all__ = ["AddUserCommand"]


class AddUserCommand(BaseJujuCommand):
    """Add user command."""

    async def execute(
        self, controller: Controller, *args: Any, overwrite: bool = False, **kwargs: Any
    ) -> Union[Dict[str, str], Result]:
        password = kwargs["password"]
        if len(password) == 0:
            password = random_password()

        try:
            user = await controller.add_user(
                username=kwargs["user"],
                password=password,
                display_name=kwargs["display_name"],
            )
        except JujuError as err:
            if overwrite:
                user = await controller.get_user(username=kwargs["user"])
                await user.set_password(password)  # Reset user's password
            else:
                raise err

        enable_cmd = EnableUserCommand()
        enable_cmd_result = await enable_cmd.run(
            controller=controller, overwrite=overwrite, **kwargs
        )
        if not enable_cmd_result.success and not overwrite:
            return enable_cmd_result

        if kwargs.get("acl"):
            try:
                grant_cmd = GrantCommand()
                grant_cmd_result: Result = await grant_cmd.run(
                    controller=controller, overwrite=overwrite, **kwargs
                )
                if not grant_cmd_result.success and not overwrite:
                    return grant_cmd_result
            except JujuError as err:
                if not overwrite:
                    raise err

        return {
            "user": user.username,
            "display_name": user.display_name,
            "password": password,
        }
