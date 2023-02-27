"""Basic logic of showing controller information.

Provides different ways to run the Juju command:

    - Batch: 20 commands in 5 parallel
    - Parallel: 20 in parallel
    - Serial: 20 commands in 1 parallel
"""
import logging
from argparse import Namespace
from dataclasses import asdict
from typing import Any, Dict, List

from juju_spell.commands.base import BaseJujuCommand, Result
from juju_spell.config import Config, Controller
from juju_spell.connections import connect_manager, get_controller

logger = logging.getLogger(__name__)

RESULT_TYPE = Dict[str, Dict[str, Any]]
RESULTS_TYPE = List[RESULT_TYPE]


def get_result(controller_config: Controller, output: Result) -> RESULT_TYPE:
    """Get command result."""
    return {
        "context": {
            "uuid": controller_config.uuid,
            "name": controller_config.name,
            "customer": controller_config.customer,
        },
        **asdict(output),
    }


async def run_parallel(
    config: Config, command: BaseJujuCommand, parsed_args: Namespace
) -> RESULTS_TYPE:
    """Run controller target command in parallel.

    THIS FUNCTION IS NOT YET SUPPORTED.
    """
    raise NotImplementedError("running in parallel is not yet supported")


async def run_serial(
    config: Config, command: BaseJujuCommand, parsed_args: Namespace
) -> RESULTS_TYPE:
    """Run controller target command serially.

    Parameters:
        config(Config): application configuration
        command(BaseJujuCommand): command to run
        parsed_args(Namespace): Namespace from CLI
    Returns:
        results(Dict): Controller dict with result.
    """
    results: RESULTS_TYPE = []
    for controller_config in config.controllers:
        controller = await get_controller(controller_config)
        logger.debug("%s running in serial", controller.controller_uuid)
        command_kwargs = vars(parsed_args)
        command_kwargs["controller_config"] = controller_config

        pre_check = await command.pre_check(controller=controller, **command_kwargs)

        if pre_check is not None:
            output = pre_check
        elif parsed_args.dry_run:
            output = await command.dry_run(controller=controller, **command_kwargs)
        else:
            output = await command.run(controller=controller, **command_kwargs)

        result = get_result(controller_config, output)
        results.append(result)

    return results


async def run_batch(
    config: Config, command: BaseJujuCommand, parsed_args: Namespace
) -> RESULTS_TYPE:
    """Run controller target command in batches.

    THIS FUNCTION IS NOT YET SUPPORTED.
    """
    raise NotImplementedError("running in batches is not yet supported")


async def run(config: Config, command: BaseJujuCommand, parsed_args: Namespace) -> RESULTS_TYPE:
    try:
        run_type = parsed_args.run_type
        logger.info("running with run_type: %s", run_type)
        if run_type == "parallel":
            return await run_parallel(config, command, parsed_args)
        if run_type == "batch":
            return await run_batch(config, command, parsed_args)

        return await run_serial(config, command, parsed_args)
    finally:
        await connect_manager.clean()
