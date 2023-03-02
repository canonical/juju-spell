from unittest.mock import AsyncMock, Mock

import pytest

from juju_spell.commands.list_models import ListModelsCommand


@pytest.mark.asyncio
async def test_execute_with_refresh():
    """Test execute function for ListModelsCommand with --refresh."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    outputs = await list_models.execute(
        controller=mock_controller,
        refresh=True,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_awaited_once()
    assert outputs["refresh"] is True


@pytest.mark.asyncio
async def test_execute_without_refresh():
    """Test execute function for ListModelsCommand without --refresh."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    outputs = await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_not_awaited()
    assert outputs["refresh"] is False
    # TODO: test caching logic
