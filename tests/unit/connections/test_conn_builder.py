from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import tenacity
from juju.errors import JujuAPIError, JujuConnectionError

from juju_spell.config import RetryPolicy
from juju_spell.settings import DEFAULT_CONNECTIN_WAIT, DEFUALT_MAX_FRAME_SIZE


@pytest.mark.asyncio
async def test_build_controller_conn():
    """Test direct connection to controller with reties."""
    from juju_spell.connections.conn_builder import build_controller_conn

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = [JujuConnectionError, None]
    uuid = uuid4()
    name = "test"
    retry_policy = RetryPolicy(attempt=2)

    await build_controller_conn(
        mock_controller,
        uuid,
        name,
        "localhost:1234",
        "user",
        "password",
        "ca_cert",
        retry_policy,
    )

    mock_controller._connector.connect.assert_has_awaits(
        [
            mock.call(
                max_frame_size=DEFUALT_MAX_FRAME_SIZE,
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
async def test_build_controller_conn_exception():
    """Test direct connection to controller with reties."""
    from juju_spell.connections.conn_builder import build_controller_conn

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = JujuAPIError(MagicMock())
    uuid = uuid4()
    name = "test"

    with pytest.raises(JujuAPIError):
        await build_controller_conn(
            mock_controller, uuid, name, "localhost:1234", "user", "password", "ca_cert"
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "retry_policy,exp_args",
    [
        (RetryPolicy(timeout=None, attempt=None, wait=None), {}),
        (
            RetryPolicy(attempt=10, timeout=None, wait=None),
            {"stop_func": tenacity.stop_any(*[tenacity.stop_after_attempt(10)])},
        ),
        (
            RetryPolicy(attempt=None, timeout=10, wait=None),
            {"stop_func": tenacity.stop_any(*[tenacity.stop_after_delay(10)])},
        ),
        (
            RetryPolicy(attempt=None, timeout=None, wait=10),
            {
                "wait_func": tenacity.wait_fixed(10),
            },
        ),
        (
            RetryPolicy(attempt=10, timeout=11, wait=12),
            {
                "stop_func": tenacity.stop_any(
                    *[
                        tenacity.stop_after_attempt(10),
                        tenacity.stop_after_delay(11),
                    ]
                ),
                "wait_func": tenacity.wait_fixed(12),
            },
        ),
    ],
)
@mock.patch("juju_spell.connections.conn_builder.tenacity.wait_fixed")
@mock.patch("juju_spell.connections.conn_builder.tenacity.retry_any")
@mock.patch("juju_spell.connections.conn_builder.tenacity.stop_any")
@mock.patch("juju_spell.connections.conn_builder._conn")
async def test_build_controller_conn_retry_policy(
    mock_conn, mock_stop_any, mock_retry_any, mock_wait_fixed, retry_policy, exp_args
):
    from juju_spell.connections.conn_builder import build_controller_conn

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = None

    default = {
        "stop_func": tenacity.stop_any(*[]),
        "wait_func": tenacity.wait_fixed(DEFAULT_CONNECTIN_WAIT),
        "retry_func": tenacity.retry_any(*[tenacity.retry_if_exception_type(JujuConnectionError)]),
    }
    exp_args = {**default, **exp_args}

    mock_stop_any.return_value = exp_args["stop_func"]
    mock_retry_any.return_value = exp_args["retry_func"]
    mock_wait_fixed.return_value = exp_args["wait_func"]

    params = {
        "controller": mock_controller,
        "uuid": uuid4(),
        "name": "test",
        "endpoint": "localhost:1234",
        "username": "user",
        "password": "password",
        "cacert": "ca_cert",
    }

    await build_controller_conn(
        **params,
        retry_policy=retry_policy,
    )

    mock_conn.assert_has_awaits(
        [
            mock.call(
                **params,
                **exp_args,
            )
        ]
    )


@pytest.mark.asyncio
@mock.patch("juju_spell.connections.conn_builder.Retrying")
@mock.patch("juju_spell.connections.conn_builder._after_log")
@mock.patch("juju_spell.connections.conn_builder._before_log")
async def test_conn(mock_before_log, mock_after_log, mock_retrying):
    from juju_spell.connections.conn_builder import _conn

    mock_controller = AsyncMock()
    mock_controller._connector.connect.side_effect = None

    params = {
        "controller": mock_controller,
        "uuid": uuid4(),
        "name": "test",
        "endpoint": "localhost:1234",
        "username": "user",
        "password": "password",
        "cacert": "ca_cert",
        "stop_func": tenacity.stop_any(tenacity.stop_after_delay(1)),
        "wait_func": tenacity.wait_fixed(1),
        "retry_func": tenacity.retry_any(*[tenacity.retry_if_exception_type(JujuConnectionError)]),
    }
    await _conn(**params)

    mock_retrying.assert_called_once_with(
        stop=params["stop_func"],
        retry=params["retry_func"],
        wait=params["wait_func"],
        reraise=True,
        after=mock_after_log.return_value,
        before=mock_before_log.return_value,
    )
