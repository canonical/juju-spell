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

"""JujuSpell tests for base juju command."""
from unittest import mock

import pytest

from juju_spell.exceptions import JujuSpellError


class TestBaseJujuCommand:
    def test_init(self, test_juju_command):
        """Test BaseJujuCommand initialization."""
        assert test_juju_command.name == "TestJujuCommand"
        assert test_juju_command.logger.name == test_juju_command.name

    @pytest.mark.asyncio
    async def test_dry_run(self, test_juju_command):
        controller = mock.MagicMock()
        controller.controller_uuid = "abc"
        test_juju_command.execute.__doc__ = "exec_doc"
        result = await test_juju_command.dry_run(controller)
        assert result.success
        assert result.output == {
            "target": "abc",
            "command_doc": "exec_doc",
        }

    @pytest.mark.asyncio
    async def test_pre_check(self, test_juju_command):
        """Test pre_check function."""
        controller = mock.MagicMock()
        controller.is_connected.return_value = True

        result = await test_juju_command.pre_check(controller)

        assert result is None

    @pytest.mark.asyncio
    async def test_pre_check_failed(self, test_juju_command):
        """Test failure of pre_check function."""
        controller = mock.MagicMock()
        controller.controller_uuid = "1234"
        controller.is_connected.return_value = False

        result = await test_juju_command.pre_check(controller)

        assert result is not None
        assert result.success is False
        assert isinstance(result.error, JujuSpellError)
        assert str(result.error) == "controller 1234 is not connected"

    @pytest.mark.asyncio
    async def test_run(self, test_juju_command):
        """Test run function."""
        test_juju_command.execute.return_value = exp_output = {"test": "value"}

        result = await test_juju_command.run(mock.MagicMock())

        assert result.success is True
        assert result.output == exp_output
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_exception(self, test_juju_command):
        """Test failure in run function."""
        test_juju_command.execute.side_effect = exp_error = Exception("test")

        result = await test_juju_command.run(mock.MagicMock())

        assert result.success is False
        assert result.output is None
        assert result.error == exp_error
