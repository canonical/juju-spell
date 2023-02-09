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
import argparse
from unittest import mock

from juju_spell.cli import RemoveUserCMD


def test_fill_parser():
    """Test add additional CLI arguments with BaseJujuCMD."""
    parser = mock.MagicMock(spec=argparse.ArgumentParser)

    cmd = RemoveUserCMD(None)
    cmd.fill_parser(parser)

    # This one is to check the basic arguments is been added.
    assert parser.add_argument.call_count == 7
    parser.add_argument.assert_has_calls(
        [
            mock.call("--user", type=str, help="username to remove", required=True),
        ]
    )
