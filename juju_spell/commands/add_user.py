"""Command to add users."""
from typing import Any, Dict, Union

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand, Result
from juju_spell.commands.grant import GrantCommand
from juju_spell.utils import random_password

__all__ = ["AddUserCommand"]


class AddUserCommand(BaseJujuCommand):
    """Add user command."""

    async def execute(
        self, controller: Controller, *args: Any, **kwargs: Any
    ) -> Union[Dict[str, str], Result]:
        password = kwargs["password"]
        if len(password) == 0:
            password = random_password()

        user = await controller.add_user(
            username=kwargs["user"],
            password=password,
            display_name=kwargs["display_name"],
        )

        if kwargs.get("acl"):
            grant_cmd = GrantCommand()
            grant_result: Result = await grant_cmd.run(controller=controller, **kwargs)
            if not grant_result.success:
                return grant_result

        return {
            "user": user.username,
            "display_name": user.display_name,
            "password": password,
        }
