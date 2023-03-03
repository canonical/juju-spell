from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from juju_spell.commands.add_user import AddUserCommand
from juju_spell.config import _validate_config


@pytest.mark.asyncio
async def test_add_user_execute(test_config_dict):
    """Check add_user cmd execute."""
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


@pytest.mark.asyncio
@patch("juju_spell.commands.add_user.GrantCommand")
@pytest.mark.parametrize(
    "acl,grant_result_success",
    [
        ("superuser", True),
        ("superuser", False),
    ],
)
async def test_add_user_execute_grant(mock_grant_cmd, test_config_dict, acl, grant_result_success):
    """Check if grant cmd has been called when acl is in params."""
    cmd = AddUserCommand()
    mock_conn = AsyncMock()

    mock_user = MagicMock()
    mock_conn.add_user.return_value = mock_user
    mock_user.username = "new-user"
    mock_user.display_name = "new-user-display-name"

    mock_grant_result = AsyncMock()
    mock_grant_result.success = grant_result_success

    _mock_grant_cmd = AsyncMock()
    mock_grant_cmd.return_value = _mock_grant_cmd
    _mock_grant_cmd.run.return_value = mock_grant_result

    controller = _validate_config(test_config_dict).controllers[0]
    output = await cmd.execute(
        mock_conn,
        **{
            "user": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
            "controller_config": controller,
            "acl": acl,
        }
    )

    _mock_grant_cmd.run.assert_awaited_once_with(
        controller=mock_conn,
        **{
            "user": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
            "controller_config": controller,
            "acl": acl,
        }
    )
    if grant_result_success:
        assert output == {
            "user": "new-user",
            "display_name": "new-user-display-name",
            "password": "new-user-pwd",
        }
    else:
        assert output == mock_grant_result
