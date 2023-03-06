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
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from juju_spell.commands.remove_user import RemoveUserCommand
from juju_spell.config import Controller
from tests.unit.utils import _async_generator


@pytest.mark.asyncio
@patch("juju_spell.commands.remove_user.DisableUserCommand")
@patch("juju_spell.commands.remove_user.RevokeCommand")
@patch("juju_spell.commands.remove_user.RevokeModelCommand")
@patch("juju_spell.commands.base.BaseJujuCommand.get_filtered_models")
async def test_remove_user_execute(
    # mock_disable_cmd, mock_revoke_cmd, mock_revoke_model_cmd,  mock_models,
    mock_models,
    mock_revoke_model_cmd,
    mock_revoke_cmd,
    mock_disable_cmd,
):
    """Test execute function for RemoveUserCommand."""
    cmd = RemoveUserCommand()

    models = [("model1", AsyncMock()), ("model2", AsyncMock())]

    controller_config = MagicMock(Controller)
    controller_config.model_mapping = None
    mock_models.return_value = _async_generator(models)

    _mock_revoke_cmd = AsyncMock()
    mock_revoke_cmd.return_value = _mock_revoke_cmd

    _mock_revoke_model_cmd = AsyncMock()
    mock_revoke_model_cmd.return_value = _mock_revoke_model_cmd

    _mock_disable_cmd = AsyncMock()
    mock_disable_cmd.return_value = _mock_disable_cmd

    mock_conn = AsyncMock()

    user = "user-a"
    output = await cmd.execute(
        mock_conn,
        **{
            "models": models,
            "controller_config": controller_config,
            "user": user,
        }
    )
    assert output is True
    _mock_revoke_cmd.run.assert_awaited_once_with(controller=mock_conn, user=user, acl="login")

    _mock_revoke_model_cmd.run.assert_has_awaits(
        [
            call(controller=mock_conn, user=user, model_uuid=models[0][-1].uuid, acl="read"),
            call(controller=mock_conn, user=user, model_uuid=models[1][-1].uuid, acl="read"),
        ]
    )
    _mock_disable_cmd.run.assert_awaited_once_with(
        controller=mock_conn,
        user=user,
    )
