"""Command to add users."""
from typing import Any, Dict

from juju.controller import Controller

from juju_spell.commands.base import BaseJujuCommand
from juju_spell.utils import random_password

__all__ = ["AddUserCommand"]


class AddUserCommand(BaseJujuCommand):
    """Add user command."""

    async def execute(self, controller: Controller, *args: Any, **kwargs: Any) -> Dict[str, str]:
        password = kwargs["password"]
        if len(password) == 0:
            password = random_password()

        user = await controller.add_user(
            username=kwargs["user"],
            password=password,
            display_name=kwargs["display_name"],
        )

        return {
            "user": user.username,
            "display_name": user.display_name,
            "password": password,
        }
