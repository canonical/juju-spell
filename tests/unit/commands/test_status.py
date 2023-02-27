from typing import AsyncGenerator, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from juju_spell.commands.status import StatusCommand
from juju_spell.config import Controller


async def _async_generator(values: List) -> AsyncGenerator:
    """Async generator."""
    for value in values:
        yield value


@pytest.mark.asyncio
@patch("juju_spell.commands.base.BaseJujuCommand.get_filtered_models")
async def test_execute(mocked_models):
    """Test execute function for StatusCommand."""
    models = [("model1", AsyncMock()), ("model2", AsyncMock())]
    controller_config = MagicMock(Controller)
    controller_config.model_mapping = None
    mocked_models.return_value = _async_generator(models)
    status = StatusCommand()

    results = await status.execute(MagicMock(), models, **{"controller_config": controller_config})

    assert len(results) == len(models)
    for name, model in models:
        assert results[name] == model.get_status.return_value
        model.get_status.assert_awaited_once()
