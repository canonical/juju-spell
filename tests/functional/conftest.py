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
"""JujuSpell configuration for functional tests."""
from typing import Generator, Tuple

import pytest

from tests.functional.setup_lxd import clean_environment, setup_environment


def pytest_addoption(parser):
    parser.addoption(
        "--cloud",
        type=str,
        default=None,
        help="Set cloud",
    )
    parser.addoption(
        "--controller",
        type=str,
        default=None,
        help="Set controller",
    )


# TODO: add marker
# TODO: run as async fixture
@pytest.fixture(scope="module")
def remote_controllers(request) -> Generator[Tuple[str, str], None, None]:
    """Return multiple controllers with all necessary configuration."""
    cloud = request.config.getoption("--cloud")
    controller_name = request.config.getoption("--controller")

    controllers = setup_environment(cloud, controller_name)
    yield controllers
    clean_environment(*controllers)
