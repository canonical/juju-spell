from unittest.mock import AsyncMock

import pytest

from juju_spell.commands.base import BaseJujuCommand


class TestJujuCommand(BaseJujuCommand):
    execute = AsyncMock()


@pytest.fixture
def test_juju_command():
    """Return test juju command object."""
    command = TestJujuCommand()
    command.execute.reset_mock()
    yield command
