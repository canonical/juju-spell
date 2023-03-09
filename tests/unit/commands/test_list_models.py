from unittest.mock import AsyncMock, Mock, patch

import pytest

import juju_spell.commands.list_models
from juju_spell.commands import list_models
from juju_spell.commands.list_models import ListModelsCommand
from juju_spell.exceptions import JujuSpellError


@pytest.mark.asyncio
@patch.object(juju_spell.commands.list_models.FileCache, "commit")
async def test_execute_with_refresh(mock_commit):
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

    mock_commit.assert_called_once()
    mock_controller.list_models.assert_awaited_once()
    assert context["data"]["refresh"] is True


@pytest.mark.asyncio
@patch.object(juju_spell.commands.list_models.FileCache, "connect")
async def test_10_execute_without_refresh_has_cache(mock_connect):
    """Test execute function for ListModelsCommand without --refresh and have existing cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_cache = Mock()
    mock_cache.data = {"models": []}
    mock_cache.expired = False
    mock_connect.return_value = mock_cache

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_connect.assert_called_once()
    mock_controller.list_models.assert_not_awaited()


@pytest.mark.asyncio
@patch.object(juju_spell.commands.list_models.FileCache, "commit")
@patch.object(juju_spell.commands.list_models.FileCache, "connect")
async def test_11_execute_without_refresh_no_cache(mock_connect, mock_commit):
    """Test execute function for ListModelsCommand without --refresh and no existing cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_connect.side_effect = JujuSpellError()

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_commit.assert_called_once()
    mock_connect.assert_called_once()
    mock_controller.list_models.assert_awaited_once()


@pytest.mark.asyncio
@patch.object(juju_spell.commands.list_models.FileCache, "commit")
@patch.object(juju_spell.commands.list_models.FileCache, "connect")
async def test_12_execute_without_refresh_expired_cache(mock_connect, mock_commit):
    """Test execute function for ListModelsCommand without --refresh and have expired cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_cache = Mock()
    mock_cache.data = {"models": []}
    mock_cache.expired = True
    mock_connect.return_value = mock_cache

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_commit.assert_called_once()
    mock_connect.assert_called_once()
    mock_controller.list_models.assert_awaited_once()


@patch.object(juju_spell.commands.list_models.FileCache, "commit")
def test_20_save_cache_data_okay(mock_commit):
    """Test save_cache_data function when save cache is okay."""
    mock_models = Mock()
    mock_logger = Mock()

    list_models.save_cache_data(Mock(), mock_models, Mock(), mock_logger, Mock())

    mock_logger.debug.assert_called_once()
    mock_logger.warning.assert_not_called()
    mock_commit.assert_called_once()


@patch.object(juju_spell.commands.list_models.FileCache, "commit")
def test_21_save_cache_data_fail(mock_commit):
    """Test save_cache_data function when save cache is not okay."""
    mock_models = Mock()
    mock_logger = Mock()

    mock_commit.side_effect = JujuSpellError()
    list_models.save_cache_data(Mock(), mock_models, Mock(), mock_logger, Mock())

    mock_logger.debug.assert_not_called()
    mock_logger.warning.assert_called_once()
    mock_commit.assert_called_once()


@patch.object(juju_spell.commands.list_models.FileCache, "connect")
def test_30_load_cache_data_okay(mock_connect):
    """Test load_cache_data function when load cache is okay."""
    mock_uuid = Mock()
    mock_name = Mock()
    mock_logger = Mock()

    list_models.load_cache_data(mock_name, mock_logger, mock_uuid)

    mock_logger.debug.assert_called_once()
    mock_logger.warning.assert_not_called()
    mock_connect.assert_called_once()


@patch.object(juju_spell.commands.list_models.FileCache, "connect")
def test_31_load_cache_data_fail(mock_connect):
    """Test load_cache_data function when load cache is not okay."""
    mock_uuid = Mock()
    mock_name = Mock()
    mock_logger = Mock()

    mock_connect.side_effect = JujuSpellError()
    list_models.load_cache_data(mock_name, mock_logger, mock_uuid)

    mock_logger.debug.assert_not_called()
    mock_logger.warning.assert_called_once()
    mock_connect.assert_called_once()
