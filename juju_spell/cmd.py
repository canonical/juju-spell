"""Module combinates all the commands."""
import argparse
import contextlib
import inspect
import logging
import os
import sys
from typing import Any, List

from craft_cli import (
    ArgumentParsingError,
    CommandGroup,
    CraftError,
    Dispatcher,
    EmitterMode,
    GlobalArgument,
    ProvideHelpException,
    emit,
)

from juju_spell import cli, utils
from juju_spell.cli.base import JujuReadCMD, JujuWriteCMD
from juju_spell.config import load_config
from juju_spell.exceptions import JujuSpellError
from juju_spell.settings import (
    APP_NAME,
    APP_VERSION,
    CONFIG_PATH,
    CROSS_FINGERS,
    PERSONAL_CONFIG_PATH,
)

GLOBAL_ARGS = [
    GlobalArgument("version", "flag", None, "--version", "Show the application version and exit"),
    GlobalArgument("config", "option", "-c", "--config", "Set the path to custom config."),
    GlobalArgument("cross-fingers", "flag", None, "--cross-fingers", argparse.SUPPRESS),
]


def get_all_subclasses(cls: Any) -> List[object]:
    """Get all subclasses of class."""
    all_classes = inspect.getmembers(cli, inspect.isclass)
    return [obj for _, obj in all_classes if issubclass(obj, cls) and obj != cls]


def get_command_groups() -> List[CommandGroup]:
    """Get grouped commands."""
    ro_commands = get_all_subclasses(JujuReadCMD)
    rw_commands = get_all_subclasses(JujuWriteCMD)
    command_groups = [
        CommandGroup("ReadOnly", ro_commands),
        CommandGroup("ReadWrite", rw_commands),
    ]

    return command_groups


def get_verbosity() -> EmitterMode:
    """Return the verbosity level to use.

    if SNAPCRAFT_ENABLE_DEVELOPER_DEBUG is set, the
    default verbosity will be set to EmitterMode.DEBUG.
    If stdin is closed, the default verbosity will be
    set to EmitterMode.VERBOSE.
    """
    verbosity = EmitterMode.BRIEF

    if not sys.stdin.isatty():
        verbosity = EmitterMode.VERBOSE

    with contextlib.suppress(ValueError):
        # Parse environment variable for backwards compatibility with launchpad
        if utils.strtobool(os.getenv("JUJUSPELL_ENABLE_DEVELOPER_DEBUG", "n").strip()):
            verbosity = EmitterMode.DEBUG

    # if defined, use environmental variable SNAPCRAFT_VERBOSITY_LEVEL
    verbosity_env = os.getenv("JUJUSPELL_VERBOSITY_LEVEL")
    if verbosity_env:
        try:
            verbosity = EmitterMode[verbosity_env.strip().upper()]
        except KeyError:
            values = utils.humanize_list([e.name.lower() for e in EmitterMode], "and", sort=False)
            raise ArgumentParsingError(
                f"cannot parse verbosity level {verbosity_env!r} from environment "
                f"variable SNAPCRAFT_VERBOSITY_LEVEL (valid values are {values})"
            ) from KeyError

    return verbosity


def get_dispatcher() -> Dispatcher:
    """Return an instance of Dispatcher.

    Run all the checks and setup required to ensure the Dispatcher can run.
    """
    verbosity = get_verbosity()
    emit.init(verbosity, APP_NAME, f"Starting {APP_NAME} app {APP_VERSION}.")

    # configure logging
    logger = logging.getLogger()
    # set root logger to debug level so that all messages are sent to Emitter
    logger.setLevel(logging.DEBUG)

    emit.debug(f"verbosity is set to {verbosity}")
    return Dispatcher(
        APP_NAME,
        get_command_groups(),
        summary="One juju to rule them all.",
        extra_global_args=GLOBAL_ARGS,
    )


def _run_dispatcher(dispatcher: Dispatcher) -> None:
    """Run Dispatcher for JujuSpell.

    This function checks whether the `-v/--version' flag is present in the CLI
    arguments, if it is present in a command, it will print the version and continue,
    on the contrary, if the flag is used alone, it will print a message and end the
    function. Next, dispatcher.pre_parse_args will be called, the app config will be
    loaded (from default path or via `--config` CLI argument), the command will be
    loaded with dispatcher and finally the dispatcher will be run.
    """
    # Check if -v or --version was provided
    args, filtered_params = dispatcher._parse_options(  # pylint: disable=W0212
        dispatcher.global_arguments, sys.argv[1:]
    )
    if args.get("version"):
        emit.message(f"JujuSpell: {APP_VERSION}")
        if not filtered_params:
            return  # exit if no command was provided

    # magic for --cross-fingers
    if args.get("cross-fingers"):
        sys.argv.append("--no-confirm")  # add --no-confirm
        print(CROSS_FINGERS, file=sys.stdout)

    global_args = dispatcher.pre_parse_args(sys.argv[1:])
    if global_args.get("config"):
        config = load_config(global_args["config"])
    else:
        config = load_config(CONFIG_PATH, PERSONAL_CONFIG_PATH)

    dispatcher.load_command(config)
    dispatcher.run()


def exec_cmd() -> int:
    """Execute craft cli."""
    dispatcher = get_dispatcher()
    return_code = 0

    try:
        _run_dispatcher(dispatcher)
        emit.ended_ok()
    except ArgumentParsingError as error:
        print(error, file=sys.stderr)  # to stderr, as argparse normally does
        emit.ended_ok()
        return_code = 127
    except ProvideHelpException as error:
        print(error, file=sys.stderr)  # to stderr, as argparse normally does
        emit.ended_ok()
        return_code = 0
    except JujuSpellError as error:
        print(str(error), file=sys.stderr)  # to stderr, as argparse normally does
        emit.ended_ok()
        return_code = 1
    except CraftError as err:
        emit.error(err)
        return_code = 1
    except KeyboardInterrupt as exc:
        craft_error = CraftError("Interrupted.")
        craft_error.__cause__ = exc
        emit.error(craft_error)
        return_code = 130
    except Exception as exc:  # pylint: disable=W0718
        craft_error = CraftError(f"Application internal error: {exc!r}")
        craft_error.__cause__ = exc
        emit.error(craft_error)
        return_code = 1

    return return_code
