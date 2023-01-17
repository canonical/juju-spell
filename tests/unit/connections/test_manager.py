import io
import unittest
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from juju_spell import config as juju_spell_config
from tests.unit.conftest import TEST_CONFIG, TEST_PERSONAL_CONFIG


@mock.patch("juju_spell.connections.connect_manager")
def test_connect_manager(mock_connect_manager):
    """Test predefined connect_manager object."""
    from juju_spell.connections import connect_manager

    assert connect_manager == mock_connect_manager


@mock.patch("juju_spell.connections.connect_manager")
def test_get_controller(mock_connect_manager, controller_config):
    """Test symlink for get_controller."""
    from juju_spell.connections import connect_manager

    connect_manager.get_controller(controller_config)
    mock_connect_manager.get_controller.assert_called_once_with(controller_config)


class TestConnectManager(unittest.IsolatedAsyncioTestCase):
    """Test case for ConnectManager class."""

    def setUp(self) -> None:
        """Set up before each test."""
        from juju_spell.connections import ConnectManager, connect_manager

        connect_manager._manager = None  # restart connect_manager
        self.connect_manager = ConnectManager()
        # NOTE: `@pytest.mark.usefixtures("controller_config")` do not work with
        # `IsolatedAsyncioTestCase`
        config = juju_spell_config.merge_configs(
            yaml.safe_load(io.StringIO(TEST_CONFIG)),
            yaml.safe_load(io.StringIO(TEST_PERSONAL_CONFIG)),
        )
        config["controllers"][0]["connection"] = juju_spell_config.Connection(
            **config["controllers"][0]["connection"]
        )
        self.controller_config_1 = juju_spell_config.Controller(
            **config["controllers"][0]
        )  # with connection
        self.controller_config_2 = juju_spell_config.Controller(
            **config["controllers"][1]
        )  # without connection

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.connect_manager.connections.clear()

    def test_new_object(self):
        """Test get new object."""
        from juju_spell.connections.manager import ConnectManager

        connect_manager1 = ConnectManager()
        connect_manager1.connections["test"] = MagicMock()
        connect_manager2 = ConnectManager()

        self.assertEqual(connect_manager1, connect_manager2)
        self.assertEqual(connect_manager1.connections, connect_manager2.connections)

    @mock.patch("juju_spell.connections.manager.juju.Controller")
    async def test_connect(self, mock_controller):
        """Test connection with direct access."""
        config = self.controller_config_2
        port_range = range(17071, 17170)
        exp_endpoint = "localhost:17071"

        mocked_controller = mock_controller.return_value = AsyncMock()
        with mock.patch(
            "juju_spell.connections.manager.get_connection"
        ) as mock_get_connection:
            mock_get_connection.return_value = exp_endpoint, MagicMock()
            controller = await self.connect_manager._connect(config, port_range)
            mock_get_connection.assert_called_once_with(config, port_range, False)

        assert controller == mocked_controller
        mocked_controller.connect.assert_called_once_with(
            endpoint=exp_endpoint,
            username=config.username,
            password=config.password,
            cacert=config.ca_cert,
        )
        assert config.name in self.connect_manager.connections

    async def test_clean(self):
        """Test clean function."""
        from juju_spell.connections.manager import Connection

        # define mocked connections
        connections = []
        for i in range(10):
            connection = Connection(AsyncMock(), MagicMock())
            self.connect_manager.connections[f"test-{i}"] = connection
            connections.append(connection)

        assert len(self.connect_manager.connections) == 10

        # test clean functions
        await self.connect_manager.clean()
        assert len(self.connect_manager.connections) == 0
        for connection in connections:
            connection.controller.disconnect.awaited_once()
            connection.connection_process.clean.assert_called_once()

    async def test_get_controller_invalid_controller_config(self):
        """Test function to get controller with invalid controller config."""
        with pytest.raises(AssertionError):
            await self.connect_manager.get_controller({"name": "test"})

    async def test_get_controller_new_controller(self):
        """Test function to get controller."""
        config = self.controller_config_1
        self.connect_manager._connect = mock_connect = AsyncMock()

        controller = await self.connect_manager.get_controller(config, reconnect=False)

        mock_connect.assert_called_once_with(config, range(17071, 17170), False)
        assert controller == mock_connect.return_value

    async def test_get_controller_reconnect(self):
        """Test function to get controller with reconnection."""
        config = self.controller_config_1
        self.connect_manager._connect = mock_connect = AsyncMock()
        self.connect_manager.connections[config.name] = mocked_connection = AsyncMock()
        mocked_connection.controller.is_connected = lambda: True

        controller = await self.connect_manager.get_controller(config, reconnect=True)

        mocked_connection.controller.disconnect.assert_called_once()
        mock_connect.assert_called_once_with(config, range(17071, 17170), False)
        assert controller == mock_connect.return_value

    async def test_get_controller_auto_reconnect(self):
        """Test function to get controller with auto reconnection."""
        config = self.controller_config_1
        self.connect_manager._connect = mock_connect = AsyncMock()
        mocked_connection = AsyncMock()
        mocked_connection.controller = mock_controller = MagicMock()
        mock_controller.is_connected.return_value = False
        self.connect_manager.connections[config.name] = mocked_connection

        controller = await self.connect_manager.get_controller(config, reconnect=False)

        mock_connect.assert_called_once_with(config, range(17071, 17170), False)
        assert controller == mock_connect.return_value

    async def test_get_controller_existing_controller(self):
        """Test function to get controller, which already exists."""
        config = self.controller_config_1
        self.connect_manager.connections[config.name] = mocked_connection = AsyncMock()
        mocked_connection.controller.is_connected = lambda: True

        controller = await self.connect_manager.get_controller(config)

        assert controller == mocked_connection.controller
