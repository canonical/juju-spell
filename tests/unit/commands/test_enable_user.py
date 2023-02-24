from unittest.mock import AsyncMock

import pytest

from juju_spell.commands.enable_user import EnableUserCommand


@pytest.mark.asyncio
async def test_enable_user_execute():
    cmd = EnableUserCommand()

    mock_conn = AsyncMock()

    await cmd.execute(mock_conn, **{"user": "new-user"})

    mock_conn.enable_user.assert_awaited_once_with(**{"username": "new-user"})
