import io
import unittest
from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import yaml
from juju.errors import JujuAPIError, JujuConnectionError

from juju_spell import config as juju_spell_config
from tests.unit.conftest import TEST_CONFIG, TEST_PERSONAL_CONFIG


@pytest.mark.parametrize(
    "attempt, retry_backoff, exp_wait",
    [
        (0, 1.5, 0.44),
        (1, 1.5, 0.67),
        (2, 1.5, 1),
        (3, 1.5, 1.5),
        (4, 1.5, 2.25),
        (5, 1.5, 3.38),
    ],
)
def test_get_wait_time(attempt, retry_backoff, exp_wait):
    """Test calculation of wait time."""
    from juju_spell.connections.manager import _get_wait_time

    wait = _get_wait_time(attempt, retry_backoff)

    assert exp_wait == round(wait, 2)


@pytest.mark.asyncio
async def test_controller_direct_connection():
    """Test direct connection to controller with reties."""
    from juju_spell.connections.manager import controller_direct_connection

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = [JujuConnectionError, None]
    uuid = uuid4()
    name = "test"

    await controller_direct_connection(
        mock_controller, uuid, name, "localhost:1234", "user", "password", "ca_cert"
    )

    mock_controller._connector.connect.assert_has_awaits(
        [
            mock.call(
                endpoint="localhost:1234",
                username="user",
                password="password",
                cacert="ca_cert",
                retries=0,
                retry_backoff=0,
            )
        ]
        * 2  # copy 2 times
    )
    assert mock_controller._connector.controller_uuid == uuid
    assert mock_controller._connector.controller_name == name


@pytest.mark.asyncio
@mock.patch("juju_spell.connections.manager.DEFAULT_CONNECTIN_TIMEOUT", new=0.5)
async def test_controller_direct_connection_timeout():
    """Test direct connection to controller with reties."""
    from juju_spell.connections.manager import controller_direct_connection

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = JujuConnectionError
    uuid = uuid4()
    name = "test"

    with pytest.raises(JujuConnectionError):
        await controller_direct_connection(
            mock_controller, uuid, name, "localhost:1234", "user", "password", "ca_cert"
        )


@pytest.mark.asyncio
async def test_controller_direct_connection_exception():
    """Test direct connection to controller with reties."""
    from juju_spell.connections.manager import controller_direct_connection

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = JujuAPIError(MagicMock())
    uuid = uuid4()
    name = "test"

    with pytest.raises(JujuAPIError):
        await controller_direct_connection(
            mock_controller, uuid, name, "localhost:1234", "user", "password", "ca_cert"
        )


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
    @mock.patch("juju_spell.connections.manager.controller_direct_connection")
    async def test_connect(self, mock_controller_direct_connection, mock_controller):
        """Test connection with direct access."""
        config = self.controller_config_2
        exp_endpoint = "localhost:17071"

        mocked_controller = mock_controller.return_value = AsyncMock()
        with mock.patch(
            "juju_spell.connections.manager.get_connection"
        ) as mock_get_connection:
            mock_get_connection.return_value = exp_endpoint, MagicMock()
            controller = await self.connect_manager._connect(config)
            mock_get_connection.assert_called_once_with(config, False)

        assert controller == mocked_controller
        mock_controller_direct_connection.assert_called_once_with(
            mocked_controller,
            uuid=config.uuid,
            name=config.name,
            endpoint=exp_endpoint,
            username=config.user,
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
            connection.controller.disconnect.assert_called_once()
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

        mock_connect.assert_called_once_with(config, False)
        assert controller == mock_connect.return_value

    async def test_get_controller_reconnect(self):
        """Test function to get controller with reconnection."""
        config = self.controller_config_1
        self.connect_manager._connect = mock_connect = AsyncMock()
        self.connect_manager.connections[config.name] = mocked_connection = AsyncMock()
        mocked_connection.controller.is_connected = lambda: True

        controller = await self.connect_manager.get_controller(config, reconnect=True)

        mocked_connection.controller.disconnect.assert_called_once()
        mock_connect.assert_called_once_with(config, False)
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

        mock_connect.assert_called_once_with(config, False)
        assert controller == mock_connect.return_value

    async def test_get_controller_existing_controller(self):
        """Test function to get controller, which already exists."""
        config = self.controller_config_1
        self.connect_manager.connections[config.name] = mocked_connection = AsyncMock()
        mocked_connection.controller.is_connected = lambda: True

        controller = await self.connect_manager.get_controller(config)

        assert controller == mocked_connection.controller
