from unittest import mock

import pytest
from craft_cli import Dispatcher

from juju_spell.cmd import GLOBAL_ARGS, _run_dispatcher, get_command_groups
from juju_spell.settings import APP_NAME, APP_VERSION, CONFIG_PATH, PERSONAL_CONFIG_PATH


@pytest.mark.parametrize(
    "cli_args",
    [
        (["--version"]),
        (["ping"]),
        (["ping", "--version"]),
        (["ping", "--config", "/tmp/config.yaml"]),
    ],
)
@mock.patch("juju_spell.cmd.sys")
@mock.patch("juju_spell.cmd.emit")
@mock.patch("juju_spell.cmd.load_config")
def test_run_dispatcher(mock_load_config, mock_emit, mock_sys, cli_args):
    """Test run dispatcher."""
    mock_sys.argv = ["juju-spell", *cli_args]

    dispatcher = Dispatcher(APP_NAME, get_command_groups(), extra_global_args=GLOBAL_ARGS)
    dispatcher.load_command = mock.MagicMock()
    dispatcher.run = mock.MagicMock()
    args, filtered_params = dispatcher._parse_options(dispatcher.global_arguments, cli_args)

    _run_dispatcher(dispatcher)

    if args.get("version") and not filtered_params:
        mock_emit.emit(f"JujuSpell: {APP_VERSION}")
    elif (args.get("version") and filtered_params) or not args.get("version"):
        mock_emit.emit(f"JujuSpell: {APP_VERSION}")

        if args.get("config"):
            mock_load_config.assert_called_once_with(args.get("config"))
        else:
            mock_load_config.assert_called_once_with(CONFIG_PATH, PERSONAL_CONFIG_PATH)

        dispatcher.load_command.assert_called_once_with(mock_load_config.return_value)
        dispatcher.run.assert_called_once()
