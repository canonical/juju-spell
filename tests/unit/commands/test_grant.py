from unittest.mock import AsyncMock

import pytest

from juju_spell.commands.grant import GrantCommand


@pytest.mark.asyncio
async def test_grant_execute():
    cmd = GrantCommand()

    mock_conn = AsyncMock()

    await cmd.execute(mock_conn, **{"user": "new-user", "acl": "superuser"})

    mock_conn.grant.assert_awaited_once_with(**{"username": "new-user", "acl": "superuser"})
