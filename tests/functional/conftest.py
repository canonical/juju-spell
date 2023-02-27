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
import logging
import os
import subprocess
from pathlib import Path
from typing import Callable, Generator
from uuid import uuid4

import pylxd.models
import pytest
from pylxd import Client

from tests.functional.setup_lxd import cleanup_environment, setup_environment

logger = logging.getLogger(__name__)


DEFAULT_SERIES = "jammy"
CLIENT_CONAINER_KEY = pytest.StashKey[str]()
CONTROLLERS_CONTAINERS_KEY = pytest.StashKey[list]()
SESSION_UUID_KEY = pytest.StashKey[str]()


def check_dependencies(*dependencies) -> None:
    """Check if dependencies are installed."""
    errors = []
    for dependency in dependencies:
        try:
            subprocess.check_output(["which", dependency])
        except subprocess.CalledProcessError:
            errors.append(f"Missing {dependency} dependency.")

    if errors:
        raise RuntimeError(os.linesep.join(errors))


def build_snap(build: bool) -> Path:
    """Build JujuSpell snap."""
    path = Path(os.environ.get("TEST_SNAP", "./juju-spell.snap"))

    if build and "TEST_SNAP" not in os.environ:
        print("snapcraft: building JujuSpell")
        subprocess.check_output(["snapcraft", "pack"])
        subprocess.check_output(["bash", "rename.sh"])

    if path.exists():
        return path

    raise RuntimeError("Something went wrong with building snap")


def pytest_addoption(parser):
    """Add custom CLI options."""
    parser.addoption(
        "--series",
        type=str,
        default=DEFAULT_SERIES,
        help="create lxd controllers with series",
    )
    parser.addoption("--no-build", action="store_false", help="flag to disable building new snap")
    parser.addoption(
        "--keep-env",
        action="store_false",
        help="flag to disable environment destroyment",
    )


def pytest_configure(config):
    """Configure environment."""
    series = config.getoption("series")
    build = config.getoption("no_build")
    keep_env = config.getoption("keep_env")
    session_uuid = str(uuid4())[:8]  # short version of uuid

    check_dependencies("juju", "lxd", "snapcraft")
    snap_path = build_snap(build)
    try:
        client, controllers = setup_environment(session_uuid, series, snap_path)
        config.stash[SESSION_UUID_KEY] = session_uuid
        config.stash[CLIENT_CONAINER_KEY] = client
        config.stash[CONTROLLERS_CONTAINERS_KEY] = controllers
        # Note (rgildein): function add_cleanup does not supports args or kwargs
        config.add_cleanup(lambda: cleanup_environment(session_uuid, keep_env))
    except Exception:
        cleanup_environment(session_uuid, keep_env)
        raise


@pytest.fixture
def session_uuid(pytestconfig) -> str:
    """Get session uuid."""
    return pytestconfig.stash[SESSION_UUID_KEY]


@pytest.fixture
def client(pytestconfig, tmp_path, controllers) -> pylxd.models.Instance:
    """Return LXD container where JujuSpell is installed."""
    name = pytestconfig.stash[CLIENT_CONAINER_KEY]
    client = Client()
    return client.instances.get(name)


@pytest.fixture
def controllers(pytestconfig) -> Generator[pylxd.models.Instance, None, None]:
    """Return LXD containers for controllers."""
    controllers = pytestconfig.stash[CONTROLLERS_CONTAINERS_KEY]
    client = Client()

    return (client.instances.get(name) for name in controllers)


@pytest.fixture
def juju_spell_run(client) -> Callable:
    """Return Callable function to execute JujuSpell command."""

    def wrapper(*args):
        result = client.execute(["juju-spell", *args], user=1000, group=1000, cwd="/home/ubuntu")
        print(
            f"LXD: command {args} finished with exit_code {result.exit_code}"
            f"{os.linesep}stdout: {result.stdout}{os.linesep}stderr: {result.stderr}"
        )
        return result

    return wrapper
