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
import asyncio
import logging
import os
import random
import subprocess
import tempfile
import textwrap
from string import ascii_lowercase
from subprocess import TimeoutExpired
from typing import Optional, Tuple

from juju import tag
from juju.client._definitions import CloudsResult
from juju.controller import Controller

logger = logging.getLogger(__name__)


def _check_juju_deps() -> str:
    """Check if Juju is installed."""
    try:
        return subprocess.check_output(["which", "juju"]).decode().strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Missing Juju dependency.") from error


def _create_controller_config(path: str):
    """Create cloudinit-userdata."""
    cloudinit = textwrap.dedent(
        """
        cloudinit-userdata: |
            postruncmd:
              - "sudo ufw deny 17070/tcp"
              - "sudo ufw --force enable"
        """
    )
    with open(path, "w") as file:
        file.write(cloudinit)


def _disable_firewall_on_controller(controller_name):
    """Disable firewall on controller."""
    # TODO: finish function
    ...


def _bootstrap_controller(cloud_name: str) -> str:
    """Bootstrap controller.

    Note(rgildein): python-libjuju does not support bootstrapping new controller
    """
    juju_path = _check_juju_deps()
    uuid = "".join(random.choice(ascii_lowercase) for _ in range(5))
    new_controller_name = f"juju-spell-func-{uuid}"
    with tempfile.NamedTemporaryFile(delete=False) as config:
        _create_controller_config(config.name)
        cmd = [
            juju_path,
            "bootstrap",
            "--verbose",
            f"--config='{config.name}'",
            cloud_name,
            new_controller_name,
        ]
        process = subprocess.check_output(cmd)
    try:
        process.wait(timeout=60 * 5)
        outs, _ = process.communicate()
        logger.info(f"bootstrapping controller was finished: {os.linesep}{outs}")
    except TimeoutExpired:
        process.kill()
        raise

    return new_controller_name


def _destroy_controller(controller_name: str) -> None:
    """Destroy controller.

    Note(rgildein): Using subprocess to avoid connection to controller, since we
    restrict direct access
    """
    juju_path = _check_juju_deps()
    cmd = [
        juju_path,
        "destroy-controller",
        "-y",
        "--destroy-all-models",
        "--force",
        controller_name,
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    process.wait(timeout=60 * 5)
    outs, _ = process.communicate()
    print(outs, _)
    logger.info(f"controller was destroy: {os.linesep}{outs}")


async def _get_lxd_cloud(controller_name: Optional[str]) -> str:
    """Get LXD cloud name."""
    controller = Controller()
    await controller.connect(controller_name=controller_name)
    clouds: CloudsResult = await controller.clouds()

    for name, cloud in clouds.clouds.items():
        if cloud.type_ == "lxd":
            return tag.untag("cloud-", name)

    raise RuntimeError("LXD cloud cloud not be found")


def setup_environment(
    cloud_name: Optional[str], controller_name: Optional[str]
) -> Tuple[str, str]:
    """Set up LXD environment.

    This function creates 2 controllers and configures them so that it is possible
    to simulate remote access.
    """
    if not cloud_name:
        cloud_name = asyncio.run(_get_lxd_cloud(controller_name))

    logger.info(f"using `{cloud_name}` cloud")

    test_controller_1 = _bootstrap_controller(cloud_name)
    test_controller_2 = _bootstrap_controller(cloud_name)

    return test_controller_1, test_controller_2


def clean_environment(*controllers):
    """Clean up LXD environment."""
    for controller in controllers:
        _destroy_controller(controller)
