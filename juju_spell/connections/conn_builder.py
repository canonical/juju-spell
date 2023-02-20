import logging
import typing as t
from uuid import UUID

import tenacity
from juju import juju
from juju.errors import JujuConnectionError
from tenacity import RetryError, Retrying

from juju_spell.config import RetryPolicy
from juju_spell.settings import DEFAULT_CONNECTIN_WAIT, DEFUALT_MAX_FRAME_SIZE

logger = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    import types  # noqa

    from tenacity.retry import RetryBaseT
    from tenacity.stop import StopBaseT
    from tenacity.wait import WaitBaseT


def _after_log(uuid, name):
    logger.info("%s connection to controller %s failed", uuid, name)


def _before_log(uuid, name):
    logger.info("Start connect to controller %s %s", uuid, name)


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
                await controller._connector.connect(
                    max_frame_size=DEFUALT_MAX_FRAME_SIZE,
                    endpoint=endpoint,
                    username=username,
                    password=password,
                    cacert=cacert,
                    retries=0,  # disable retires in connection
                    retry_backoff=0,
                )
                controller._connector.controller_uuid = uuid
                controller._connector.controller_name = name
                logger.info(f"{attempt} finish")
    except RetryError as err:
        logger.info(
            "%s connection to controller %s failed with error '%s'",
            uuid,
            name,
            err,
        )
        raise


async def build_controller_conn(
    controller: juju.Controller,
    uuid: UUID,
    name: str,
    endpoint: str,
    username: str,
    password: str,
    cacert: str,
    retry_policy: t.Optional[RetryPolicy] = None,
):
    # Apply default to retry policy if not config.
    if retry_policy is None:
        retry_policy = RetryPolicy()

    # Note(rgildein): Connection will raise JujuConnectionError if endpoint
    # is unreachable. This can happen, for example, when port forwarding is
    # through a subprocess and the process has not yet started.
    retry_funcs = [tenacity.retry_if_exception_type(JujuConnectionError)]
    wait_func: tenacity.wait.wait_base = tenacity.wait_fixed(DEFAULT_CONNECTIN_WAIT)
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
