from unittest.mock import AsyncMock, call, patch

import pytest

from juju_spell.commands.grant import GrantCommand
from juju_spell.config import _validate_config
from tests.unit.utils import _async_generator


@pytest.mark.asyncio
@patch("juju_spell.commands.grant.GrantCommand.get_filtered_models")
@pytest.mark.parametrize(
    "acl,exp_controller_acl,exp_model_acl",
    (
        ("superuser", "superuser", "admin"),
        ("superuser", "superuser", "admin"),
    ),
)
async def test_grant_execute(
    mocked_models,
    test_config_dict,
    acl,
    exp_controller_acl,
    exp_model_acl,
):
    cmd = GrantCommand()

    mock_model1 = AsyncMock()
    mock_model1.uuid = "0050e762-9002-4197-b163-64bda52427db"
    mock_model2 = AsyncMock()
    mock_model2.uuid = "ab9065d4-f762-4386-85e1-5fd892453b68"
    models = [("model1", mock_model1), ("model2", mock_model2)]
    mocked_models.return_value = _async_generator(models)

    mock_conn = AsyncMock()

    controller = _validate_config(test_config_dict).controllers[0]
    controller.model_mapping = None

    await cmd.execute(
        mock_conn,
        **{
            "user": "new-user",
            "acl": acl,
            "controller_config": controller,
        }
    )

    mock_conn.grant.assert_awaited_once_with(
        **{
            "username": "new-user",
            "acl": exp_controller_acl,
        }
    )

    mocked_models.assert_called_once_with(
        controller=mock_conn,
        models=None,
        model_mappings=None,
    )
    mock_conn.grant_model.assert_has_awaits(
        [
            call(
                username="new-user",
                model_uuid=mock_model1.uuid,
                acl=exp_model_acl,
            ),
            call(
                username="new-user",
                model_uuid=mock_model2.uuid,
                acl=exp_model_acl,
            ),
        ]
    )
