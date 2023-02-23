from unittest.mock import AsyncMock, MagicMock, call

import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "all_models, args_models, exp_models, model_mappings",
    [
        ([], ["test-model"], ["test-model"], {}),
        (["model1", "model2", "model3"], ["test-model"], ["test-model"], {}),
        (["model1", "model2", "model3"], ["model1"], ["model1"], {}),
        (
            ["model1", "model2", "model3"],
            ["model1", "model2"],
            ["model1", "model2"],
            {},
        ),
        (["model1", "model2", "model3"], [], ["model1", "model2", "model3"], {}),
        (["model1", "model2", "model3"], None, ["model1", "model2", "model3"], {}),
        (
            ["model1", "model2", "model3"],
            ["default"],
            ["model1"],
            {"lma": ["monitoring"], "default": ["model1"]},
        ),
        (
            ["model1", "model2", "model3"],
            ["default", "lma"],
            ["model1", "model2"],
            {"lma": ["model1"], "default": ["model2"]},
        ),
        (
            ["model1", "model2", "model3"],
            ["default", "lma"],
            ["modelx", "modely"],
            {"lma": ["modelx"], "default": ["modely"]},
        ),
        (
            ["model1", "model2", "model3"],
            ["model1", "default"],
            ["model1", "default"],
            {"lma": [], "default": []},
        ),
        (
            ["model1", "model2", "model3"],
            ["model1", "default"],
            ["model1", "default"],
            {},
        ),
        (
            ["model1", "model2", "model3"],
            ["model1", "default"],
            ["model1", "xx", "yy"],
            {"lma": [], "default": ["xx", "yy"]},
        ),
    ],
)
async def test_get_filtered_models_mapping(
    all_models, args_models, exp_models, model_mappings, test_juju_command
):
    """Test async models generator."""
    mock_controller = AsyncMock()
    mock_controller.list_models.return_value = all_models
    mock_controller.get_model.return_value = mock_model = AsyncMock()

    models_generator = test_juju_command.get_filtered_models(
        mock_controller, model_mappings, args_models
    )
    models = [name async for name, _ in models_generator]

    # check returned models
    assert set(models) == set(exp_models)
    # check that model was get from controller
    mock_controller.get_model.assert_has_awaits(calls=[call(name) for name in models])
    # check that model was disconnected
    assert mock_model.disconnect.await_count == len(models)


@pytest.mark.asyncio
async def test_run(test_juju_command):
    """Test run for any juju command."""
    mock_controller = MagicMock()

    await test_juju_command.run(mock_controller, test=5)

    test_juju_command.execute.assert_called_once_with(mock_controller, test=5)


def test_need_shuttle(test_juju_command):
    """Test default return value for need_shuttle property."""
    assert test_juju_command.need_sshuttle is False
