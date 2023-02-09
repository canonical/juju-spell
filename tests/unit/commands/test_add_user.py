from unittest.mock import AsyncMock, MagicMock

import pytest

from juju_spell.commands.add_user import AddUserCommand
from juju_spell.config import _validate_config


@pytest.mark.asyncio
async def test_add_user_execute(test_config_dict):
    cmd = AddUserCommand()

    mock_conn = AsyncMock()

    mock_user = MagicMock()
    mock_conn.add_user.return_value = mock_user
    mock_user.username = "new-user"
    mock_user.display_name = "new-user-display-name"

    controller = _validate_config(test_config_dict).controllers[0]
    output = await cmd.execute(
        mock_conn,
        **{
            "user": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
            "controller_config": controller,
        }
    )
    mock_conn.add_user.assert_awaited_once_with(
        **{
            "username": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
        }
    )
    assert output == {
        "user": "new-user",
        "display_name": "new-user-display-name",
        "password": "new-user-pwd",
    }
