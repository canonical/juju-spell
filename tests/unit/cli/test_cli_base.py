# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Tests for base cli functions."""
import argparse
import os
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from juju_spell.config import Controller
from juju_spell.exceptions import JujuSpellError


def test_base_cmd_fill_parser(base_cmd):
    """Test add additional CLI arguments with BaseCMD."""
    parser = MagicMock()
    base_cmd.fill_parser(parser)

    parser.assert_not_called()


def test_base_cmd_run(base_cmd):
    """Test run from BaseCMD."""
    parsed_args = argparse.Namespace(**{"test": True})
    base_cmd.before = mock_before = MagicMock()
    base_cmd.execute = mock_execute = MagicMock()
    base_cmd.format_output = mock_format_output = MagicMock()
    base_cmd.after = mock_after = MagicMock()

    assert base_cmd.run(parsed_args) == 0

    mock_before.assert_called_once_with(parsed_args)
    mock_execute.assert_called_once_with(parsed_args)
    mock_format_output.assert_called_once_with(mock_execute.return_value)
    mock_after.assert_called_once_with(parsed_args)


@patch("juju_spell.cli.base.emit")
def test_base_cmd_run_exception(mock_emit, base_cmd):
    """Test run exceptions from BaseCMD."""
    parsed_args = argparse.Namespace(**{"test": True})
    exp_error = ValueError("Some value failed")
    base_cmd.before = mock_before = MagicMock()
    mock_before.side_effect = exp_error

    with pytest.raises(JujuSpellError):
        base_cmd.run(parsed_args)


@pytest.mark.parametrize(
    "output, exp_formatted_output",
    [
        ("string", "string"),
        (True, "True"),
        (1, "1"),
        ([1, 2, 3], "[{0} 1,{0} 2,{0} 3{0}]".format(os.linesep)),
        (
            {"test": {"Gandalf": "Olorin"}},
            '{{{0} "test": {{{0}  "Gandalf": "Olorin"{0} }}{0}}}'.format(os.linesep),
        ),
    ],
)
def test_base_cmd_format_output(output, exp_formatted_output, base_cmd):
    """Test pretty formatter for output in BaseCMD."""
    assert base_cmd.format_output(output) == exp_formatted_output


@patch("juju_spell.cli.base.parse_filter")
@patch("juju_spell.cli.base.parse_comma_separated_str")
def test_base_juju_cmd_fill_parser(
    mock_parse_comma_separated_str, mock_parse_filter, base_juju_cmd
):
    """Test add additional CLI arguments with BaseJujuCMD."""
    parser = MagicMock()
    base_juju_cmd.fill_parser(parser)

    parser.add_argument.assert_has_calls(
        [
            mock.call(
                "--no-confirm",
                default=False,
                action="store_true",
                help="This will skip all the confirm check.",
            ),
            mock.call(
                "--run-type",
                type=str,
                choices=["parallel", "batch", "serial"],
                default="serial",
                help="parallel, batch or serial",
            ),
            mock.call(
                "--filter",
                type=mock_parse_filter,
                required=False,
                default="",
                help=(
                    "Key-value pair comma separated string in double quotes e.g., "
                    '"a=1,2,3 b=4,5,6". '
                ),
            ),
            mock.call("--models", type=mock_parse_comma_separated_str, help="model filter"),
        ]
    )


@pytest.mark.asyncio
@patch("juju_spell.cli.base.run", new_callable=MagicMock)
@patch("juju_spell.cli.base.asyncio")
@patch("juju_spell.cli.base.get_filtered_config")
async def test_base_juju_cmd_execute(mock_get_filtered_config, mock_asyncio, _, base_juju_cmd):
    """Test add additional CLI arguments with BaseJujuCMD."""
    parsed_args = argparse.Namespace(**{"filter": None})
    mock_asyncio.get_event_loop.return_value = loop = MagicMock()
    task = loop.create_task.return_value = MagicMock()

    result = base_juju_cmd.execute(parsed_args)

    mock_get_filtered_config.assert_called_once_with(base_juju_cmd.config, None)
    mock_asyncio.get_event_loop.assert_called_once()
    loop.create_task.assert_called_once()
    loop.run_until_complete.assert_called_once()
    assert result == task.result.return_value


def test_base_juju_cmd_execute_exception(base_juju_cmd):
    """Test add additional CLI arguments with BaseJujuCMD."""
    parsed_args = argparse.Namespace(**{"filter": None})
    base_juju_cmd.command = None

    with pytest.raises(RuntimeError):
        base_juju_cmd.execute(parsed_args)


def _create_test_controller(name: str) -> Controller:
    """Create test controller."""
    return Controller(
        uuid="fb006616-0176-41d8-8ba9-ec57bb6e141a",
        name=name,
        customer="test-customer",
        owner="test-owner",
        endpoint="10.1.1.99:17070",
        ca_cert="ca-cert",
        username="test-user",
        password="test-password",
        model_mapping={},
    )


@pytest.mark.parametrize(
    "parsed_args, confirm_return_value, executed",
    [
        ({"no_confirm": False}, True, True),
        ({"no_confirm": False}, False, False),
        ({"no_confirm": True}, True, True),
        ({"no_confirm": True}, False, True),
    ],
)
@patch("juju_spell.cli.base.BaseJujuCMD.run")
def test_juju_write_cmd_run(mock_run, parsed_args, confirm_return_value, executed, juju_write_cmd):
    """Test BaseCMD run."""
    parsed_args = argparse.Namespace(**parsed_args)
    juju_write_cmd.safe_parsed_args_output = MagicMock()

    with patch("juju_spell.cli.base.confirm", return_value=confirm_return_value):
        juju_write_cmd.run(parsed_args)

    assert (mock_run.call_count != 0) == executed
