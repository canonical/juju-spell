# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2023 Canonical Ltd.
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
"""Tests for assignment.runner."""
from argparse import Namespace
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from juju_spell.assignment.runner import get_result, pre_check, run
from juju_spell.commands.base import Result


@pytest.mark.parametrize(
    "controller_config, output, exp_result",
    [
        (
            MagicMock(),
            Result(True, "test-string-value", None),
            {
                "context": mock.ANY,
                "success": True,
                "output": "test-string-value",
                "error": None,
            },
        ),
        (
            MagicMock(),
            Result(False, "test-string-value", None),
            {
                "context": mock.ANY,
                "success": False,
                "output": "test-string-value",
                "error": None,
            },
        ),
        (
            MagicMock(),
            Result(True, 1234, None),
            {"context": mock.ANY, "success": True, "output": 1234, "error": None},
        ),
        (
            MagicMock(),
            Result(False, None, Exception("test")),
            {
                "context": mock.ANY,
                "success": False,
                "output": None,
                "error": mock.ANY,
            },
        ),
    ],
)
def test_get_result(controller_config, output, exp_result):
    """Test for get_result."""
    result = get_result(controller_config, output)
    assert result == exp_result


@pytest.mark.asyncio
@patch("juju_spell.assignment.runner.run_serial", new_callable=AsyncMock)
@patch("juju_spell.assignment.runner.run_batch")
@patch("juju_spell.assignment.runner.run_parallel")
@patch("juju_spell.assignment.runner.pre_check", new_callable=AsyncMock)
@pytest.mark.parametrize(
    "juju_cmd, parsed_args, expected_call",
    [
        (MagicMock(), Namespace(pre_check=False, run_type="serial"), False),
        (MagicMock(), Namespace(pre_check=True, run_type="serial"), True),
        (MagicMock(), Namespace(pre_check=True, run_type="batch"), True),
        (MagicMock(), Namespace(pre_check=True, run_type="parallel"), True),
    ],
)
async def test_pre_check_been_called(
    mock_precheck,
    mock_run_parallel,
    mock_run_batch,
    mock_run_serial,
    juju_cmd,
    parsed_args,
    expected_call,
    test_config,
):
    mock_precheck.return_value = (True, {})
    await run(config=test_config, command=juju_cmd, parsed_args=parsed_args)
    if expected_call:
        mock_precheck.assert_called_once_with(
            config=test_config,
            parsed_args=parsed_args,
        )
        if parsed_args.run_type == "serial":
            mock_run_serial.assert_has_calls(
                [mock.call(test_config, juju_cmd, parsed_args)]
            )
        if parsed_args.run_type == "batch":
            mock_run_batch.assert_has_calls(
                [mock.call(test_config, juju_cmd, parsed_args)]
            )
        if parsed_args.run_type == "parallel":
            mock_run_parallel.assert_has_calls(
                [mock.call(test_config, juju_cmd, parsed_args)]
            )
    else:
        mock_precheck.assert_not_called()


@pytest.mark.asyncio
@patch("juju_spell.assignment.runner.run_serial", new_callable=AsyncMock)
@patch("juju_spell.assignment.runner.run_batch")
@patch("juju_spell.assignment.runner.run_parallel")
@patch("juju_spell.assignment.runner.PingCommand")
@pytest.mark.parametrize(
    "parsed_args",
    [
        (Namespace(run_type="serial")),
        (Namespace(run_type="batch")),
        (Namespace(run_type="parallel")),
    ],
)
async def test_pre_check(
    mock_ping_cmd,
    mock_run_parallel,
    mock_run_batch,
    mock_run_serial,
    parsed_args,
    test_config,
):
    await pre_check(test_config, parsed_args)

    if parsed_args.run_type == "serial":
        mock_run_serial.assert_has_calls(
            [mock.call(test_config, mock_ping_cmd(), parsed_args)]
        )
    if parsed_args.run_type == "batch":
        mock_run_batch.assert_has_calls(
            [mock.call(test_config, mock_ping_cmd(), parsed_args)]
        )
    if parsed_args.run_type == "parallel":
        mock_run_parallel.assert_has_calls(
            [mock.call(test_config, mock_ping_cmd(), parsed_args)]
        )
