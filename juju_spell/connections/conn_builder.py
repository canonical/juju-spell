"""Module to build connection to controller."""
import logging
from typing import Callable, Optional
from uuid import UUID

import tenacity
from juju import juju
from juju.errors import JujuConnectionError
from tenacity import RetryCallState, RetryError, Retrying
from tenacity.retry import RetryBaseT
from tenacity.stop import StopBaseT
from tenacity.wait import WaitBaseT

from juju_spell.config import RetryPolicy
from juju_spell.settings import DEFAULT_CONNECTION_WAIT, DEFAULT_MAX_FRAME_SIZE

logger = logging.getLogger(__name__)


def _after_log(uuid, name) -> Callable:
    """Help function for logs after retry."""

    def log_it(retry_state: "RetryCallState") -> None:  # pylint: disable=W0613
        logger.info("%s connection to controller %s failed", uuid, name)

    return log_it


def _before_log(uuid, name) -> Callable:
    """Help function for logs before retry."""

    def log_it(retry_state: "RetryCallState") -> None:  # pylint: disable=W0613
        logger.info("Start connect to controller %s %s", uuid, name)

    return log_it


# pylint: disable=R0913
async def _conn(
    controller: juju.Controller,
    uuid: UUID,
    name: str,
    endpoint: str,
    username: str,
    password: str,
    cacert: str,
    stop_func: "StopBaseT",
    wait_func: "WaitBaseT",
    retry_func: "RetryBaseT",
):
    """Execute retry with RetryPolicy."""
    try:
        for attempt in Retrying(
            stop=stop_func,
            retry=retry_func,
            wait=wait_func,
            after=_after_log(uuid=uuid, name=name),
            before=_before_log(uuid=uuid, name=name),
            reraise=True,
        ):
            with attempt:
                await controller._connector.connect(  # pylint: disable=W0212
                    max_frame_size=DEFAULT_MAX_FRAME_SIZE,
                    endpoint=endpoint,
                    username=username,
                    password=password,
                    cacert=cacert,
                    retries=0,  # disable retires in connection
                    retry_backoff=0,
                )
                controller._connector.controller_uuid = uuid  # pylint: disable=W0212
                controller._connector.controller_name = name  # pylint: disable=W0212
                logger.info("%s finish", attempt)
    except RetryError as err:
        logger.info(
            "%s connection to controller %s failed with error '%s'",
            uuid,
            name,
            err,
        )
        raise


# pylint: disable=R0913
async def build_controller_conn(
    controller: juju.Controller,
    uuid: UUID,
    name: str,
    endpoint: str,
    username: str,
    password: str,
    cacert: str,
    retry_policy: Optional[RetryPolicy] = None,
):
    """Builder for controller connection."""
    if retry_policy is None:
        retry_policy = RetryPolicy()

    # Note(rgildein): Connection will raise JujuConnectionError if endpoint
    # is unreachable. This can happen, for example, when port forwarding is
    # through a subprocess and the process has not yet started.
    retry_funcs = [tenacity.retry_if_exception_type(JujuConnectionError)]
    wait_func: tenacity.wait.wait_base = tenacity.wait_fixed(DEFAULT_CONNECTION_WAIT)
    stop_funcs = []

    if retry_policy.attempt:
        stop_funcs.append(tenacity.stop_after_attempt(retry_policy.attempt))
    if retry_policy.wait:
        wait_func = tenacity.wait_fixed(retry_policy.wait)
    if retry_policy.timeout:
        stop_funcs.append(tenacity.stop_after_delay(retry_policy.timeout))

    await _conn(
        controller=controller,
        uuid=uuid,
        name=name,
        endpoint=endpoint,
        username=username,
        password=password,
        cacert=cacert,
        stop_func=tenacity.stop_any(*stop_funcs),
        wait_func=wait_func,
        retry_func=tenacity.retry_any(*retry_funcs),
    )
