from unittest.mock import AsyncMock

import pytest

from juju_spell.commands.list_models import ListModelsCommand


@pytest.mark.asyncio
async def test_execute_with_refresh():
    """Test execute function for ListModelsCommand with --refresh."""
    mock_controller = AsyncMock()
    list_models = ListModelsCommand()

    outputs = await list_models.execute(controller=mock_controller, refresh=True)

    mock_controller.list_models.assert_awaited_once()
    assert outputs["refresh"] is True


@pytest.mark.asyncio
async def test_execute_without_refresh():
    """Test execute function for ListModelsCommand without --refresh."""
    mock_controller = AsyncMock()
    list_models = ListModelsCommand()

    outputs = await list_models.execute(controller=mock_controller, refresh=False)

    mock_controller.list_models.assert_not_awaited()
    assert outputs["refresh"] is False
    # TODO: test caching logic
