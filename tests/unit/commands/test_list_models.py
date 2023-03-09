from unittest.mock import AsyncMock, Mock, patch

import pytest

from juju_spell.commands import list_models
from juju_spell.commands.list_models import ListModelsCommand
from juju_spell.exceptions import JujuSpellError


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.save_to_cache")
@patch("juju_spell.commands.list_models.load_from_cache")
async def test_execute_with_refresh(mock_load_from_cache, mock_save_to_cache):
    """Test execute function for ListModelsCommand with --refresh."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    context = await list_models.execute(
        controller=mock_controller,
        refresh=True,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_save_to_cache.assert_called_once()
    mock_load_from_cache.assert_not_called()
    mock_controller.list_models.assert_awaited_once()
    assert context["data"]["refresh"] is True


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.save_to_cache")
@patch("juju_spell.commands.list_models.load_from_cache")
async def test_11_execute_without_refresh_no_cache(mock_load_from_cache, mock_save_to_cache):
    """Test execute function for ListModelsCommand without --refresh and no existing cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_load_from_cache.side_effect = JujuSpellError()

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_save_to_cache.assert_called_once()
    mock_load_from_cache.assert_called_once()
    mock_controller.list_models.assert_awaited_once()


@patch("juju_spell.commands.list_models.save_to_cache")
def test_20_save_cache_data_okay(mock_save_to_cache):
    """Test save_cache_data function when save cache is okay."""
    mock_models = Mock()
    mock_logger = Mock()

    list_models.save_cache_data(Mock(), mock_models, Mock(), mock_logger, Mock())

    mock_logger.debug.assert_called_once()
    mock_logger.warning.assert_not_called()
    mock_save_to_cache.assert_called_once()


@patch("juju_spell.commands.list_models.save_to_cache")
def test_21_save_cache_data_fail(mock_save_to_cache):
    """Test save_cache_data function when save cache is not okay."""
    mock_models = Mock()
    mock_logger = Mock()

    mock_save_to_cache.side_effect = JujuSpellError()
    list_models.save_cache_data(Mock(), mock_models, Mock(), mock_logger, Mock())

    mock_logger.debug.assert_not_called()
    mock_logger.warning.assert_called_once()
    mock_save_to_cache.assert_called_once()


@patch("juju_spell.commands.list_models.load_from_cache")
def test_30_load_cache_data_okay(mock_load_from_cache):
    """Test load_cache_data function when load cache is okay."""
    mock_uuid = Mock()
    mock_name = Mock()
    mock_logger = Mock()

    list_models.load_cache_data(mock_name, mock_logger, mock_uuid)

    mock_logger.debug.assert_called_once()
    mock_logger.warning.assert_not_called()
    mock_load_from_cache.assert_called_once()


@patch("juju_spell.commands.list_models.load_from_cache")
def test_31_load_cache_data_fail(mock_load_from_cache):
    """Test load_cache_data function when load cache is not okay."""
    mock_uuid = Mock()
    mock_name = Mock()
    mock_logger = Mock()

    mock_load_from_cache.side_effect = JujuSpellError()
    list_models.load_cache_data(mock_name, mock_logger, mock_uuid)

    mock_logger.debug.assert_not_called()
    mock_logger.warning.assert_called_once()
    mock_load_from_cache.assert_called_once()
