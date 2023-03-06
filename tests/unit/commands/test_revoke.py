from unittest.mock import AsyncMock, MagicMock

import pytest

from juju_spell.commands.revoke import RevokeCommand, RevokeModelCommand


@pytest.mark.asyncio
async def test_revoke_execute():
    mock_conn = AsyncMock()

    cmd = RevokeCommand()
    output = await cmd.execute(controller=mock_conn, user="new-user", acl="superuser")
    assert output is True

    mock_conn.revoke.assert_awaited_once_with(
        username="new-user",
        acl="superuser",
    )


@pytest.mark.asyncio
async def test_revoke_model_execute():
    mock_conn = AsyncMock()
    mock_model = MagicMock()
    mock_model.uuid = "13089ea3-2cba-47c2-92d1-a33db230ea49"

    cmd = RevokeModelCommand()
    output = await cmd.execute(
        controller=mock_conn,
        user="new-user",
        acl="superuser",
        model_uuid="13089ea3-2cba-47c2-92d1-a33db230ea49",
    )
    assert output is True

    mock_conn.revoke_model.assert_awaited_once_with(
        username="new-user",
        acl="superuser",
        model_uuid="13089ea3-2cba-47c2-92d1-a33db230ea49",
    )
