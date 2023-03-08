from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from juju.errors import JujuError

from juju_spell.commands.add_user import AddUserCommand
from juju_spell.commands.base import Result
from juju_spell.config import _validate_config
from juju_spell.exceptions import JujuSpellError


@pytest.mark.asyncio
async def test_add_user_execute(test_config_dict):
    """Check add_user cmd execute."""
    cmd = AddUserCommand()

    mock_conn = AsyncMock()

    mock_conn.get_user.return_value = None

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
        },
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
@patch("juju_spell.commands.add_user.EnableUserCommand")
@patch("juju_spell.commands.add_user.GrantCommand")
@pytest.mark.parametrize(
    "acl,overwrite,grant_result",
    [
        ("superuser", False, Result(success=True)),
        ("superuser", False, Result(success=False, error=JujuSpellError())),
    ],
)
async def test_add_user_execute_grant(
    mock_grant_cmd,
    mock_enable_user_cmd,
    test_config_dict,
    acl,
    overwrite,
    grant_result,
):
    """Check if grant cmd has been called when acl is in params."""
    cmd = AddUserCommand()
    mock_conn = AsyncMock()

    mock_conn.get_user.return_value = None

    mock_user = MagicMock()
    mock_conn.add_user.return_value = mock_user
    mock_user.username = "new-user"
    mock_user.display_name = "new-user-display-name"

    _mock_grant_cmd = AsyncMock()
    mock_grant_cmd.return_value = _mock_grant_cmd
    _mock_grant_cmd.run.return_value = grant_result

    _mock_enable_user_cmd = AsyncMock()
    mock_enable_user_cmd.return_value = _mock_enable_user_cmd
    _mock_enable_user_cmd.run.return_value = Result(success=True)

    controller = _validate_config(test_config_dict).controllers[0]

    output = await cmd.execute(
        mock_conn,
        **{
            "user": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
            "controller_config": controller,
            "acl": acl,
            "overwrite": overwrite,
        },
    )

    _mock_grant_cmd.run.assert_awaited_once_with(
        controller=mock_conn,
        **{
            "user": "new-user",
            "password": "new-user-pwd",
            "display_name": "new-user-display-name",
            "controller_config": controller,
            "acl": acl,
            "overwrite": overwrite,
        },
    )
    if grant_result.success:
        assert output == {
            "user": "new-user",
            "display_name": "new-user-display-name",
            "password": "new-user-pwd",
        }
    else:
        assert output == grant_result


@pytest.mark.asyncio
@patch("juju_spell.commands.add_user.GrantCommand")
@patch("juju_spell.commands.add_user.EnableUserCommand")
@pytest.mark.parametrize(
    "overwrite",
    [
        (True),
        (False),
    ],
)
async def test_add_user_overwrite(
    mock_grant_cmd, mock_enable_user_cmd, test_config_dict, overwrite
):
    cmd = AddUserCommand()

    mock_conn = AsyncMock()
    mock_conn.add_user.side_effect = JujuError()

    mock_get_user_result = AsyncMock()
    mock_get_user_result.username = "new-user"
    mock_get_user_result.display_name = "new-user-display-name"
    mock_conn.get_user.return_value = mock_get_user_result

    _mock_grant_cmd = AsyncMock()
    mock_grant_cmd.return_value = _mock_grant_cmd
    _mock_grant_cmd.run.return_value = Result(success=False)

    _mock_enable_user_cmd = AsyncMock()
    mock_enable_user_cmd.return_value = _mock_enable_user_cmd
    _mock_enable_user_cmd.run.return_value = Result(success=False)

    controller = _validate_config(test_config_dict).controllers[0]

    if overwrite:
        output = await cmd.execute(
            mock_conn,
            **{
                "user": "new-user",
                "password": "new-user-pwd",
                "display_name": "new-user-display-name",
                "controller_config": controller,
                "acl": "superuser",
                "overwrite": overwrite,
            },
        )

        mock_conn.get_user.assert_awaited_once_with(username="new-user")
        mock_get_user_result.set_password.assert_awaited_once_with("new-user-pwd")

        assert output == {
            "user": "new-user",
            "display_name": "new-user-display-name",
            "password": "new-user-pwd",
        }
    else:
        output = await cmd.execute(
            mock_conn,
            **{
                "user": "new-user",
                "password": "new-user-pwd",
                "display_name": "new-user-display-name",
                "controller_config": controller,
                "acl": "superuser",
                "overwrite": overwrite,
            },
        )
        assert output == Result(success=False)
