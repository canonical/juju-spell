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
import json
import os
import subprocess
import textwrap
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Tuple, Union

import yaml
from pylxd import Client
from pylxd.exceptions import NotFound
from pylxd.models import Container, Instance
from pylxd.models.instance import _InstanceExecuteResult

from juju_spell.config import convert_config

CONTAINER_PREFIX = "jujuspell"
DEFAULT_DIRECTORY = Path("/home/ubuntu/.local/share/juju-spell")
SSH_CONFIG = textwrap.dedent(
    """
Host *
  StrictHostKeyChecking=accept-new
"""
)
CONTROLLER_API_PORT = 17007
NUMBER_OF_CONTROLLERS = 2
STOPPED_CONTAINER_CODE = 102
WAIT_TIMEOUT = 1
WAIT_COUNT = 10


class ExecuteError(Exception):
    ...


def get_controller(name: str) -> Dict[str, Any]:
    """Get information about controller."""
    output = subprocess.check_output(
        ["juju", "show-controller", "--show-password", "--format", "json", name]
    ).decode()
    return json.loads(output)


def lxd_execute(container: Instance, cmd: List[str], root: bool = False) -> _InstanceExecuteResult:
    """Execute on container."""
    kwargs = {}
    command = " ".join(cmd)
    if not root:
        kwargs["user"] = 1000
        kwargs["group"] = 1000
        kwargs["cwd"] = "/home/ubuntu"

    result = container.execute(cmd, **kwargs)
    print(
        f"LXD: {container.name} command `{command}` exit with {result.exit_code}"
        f"{os.linesep}  stdout: {result.stdout}{os.linesep}  stderr: {result.stderr}"
    )
    if result.exit_code != 0:
        raise ExecuteError(f"command `{command}` falied with error: {result.stderr}")

    return result


def is_alive(container: Instance) -> bool:
    """Check if container is alive."""
    try:
        lxd_execute(container, ["sudo", "snap", "refresh"])
        return True
    except (NotFound, ExecuteError):
        return False


def wait_for_container(container: Instance) -> None:
    """Wait for container to become alive."""
    for _ in range(WAIT_COUNT):
        sleep(WAIT_TIMEOUT)
        if is_alive(container):
            break

    print(f"LXD: container {container.name} is ready")


def try_unregister_controller(name: str) -> None:
    """Try to unregister controller without raising error."""
    try:
        subprocess.check_call(
            ["juju", "unregister", "-y", name],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"Juju: controller {name} was unregistered")


def create_container(session_uuid: str, name: str, series: str) -> Container:
    """Create instance."""
    client = Client()
    container_name = f"{CONTAINER_PREFIX}-{name}-{session_uuid}"
    config = {
        "name": container_name,
        "source": {
            "type": "image",
            "mode": "pull",
            "server": "https://cloud-images.ubuntu.com/daily",
            "protocol": "simplestreams",
            "alias": series,
        },
        "type": "container",
    }

    print(f"LXD: creating {name} with name: `{container_name}` and series {series}")
    container: Container = client.containers.create(config, wait=True)
    container.start(wait=True)
    print(f"LXD: {container.name} is running")
    return container


def create_client_instance(
    session_uuid: str, series: str, snap_path: Union[str, Path]
) -> Instance:
    """Create client instance."""
    client = create_container(session_uuid, "client", series)
    wait_for_container(client)

    lxd_execute(client, ["sudo", "ufw", "enable"])
    # drop direct connection to any controller, e.g. <ip>:CONTROLLER_API_PORT
    lxd_execute(client, ["sudo", "ufw", "deny", "out", str(CONTROLLER_API_PORT)])
    lxd_execute(client, ["ssh-keygen", "-q", "-f", "/home/ubuntu/.ssh/id_rsa", "-N", ""])
    with open(snap_path, "rb") as snap:
        client.files.put("/home/ubuntu/juju-spell.snap", snap.read(), uid=1000, gid=1000)

    lxd_execute(client, ["sudo", "snap", "install", "./juju-spell.snap", "--devmode"])
    # NOTE (rgildein): Right now JujuSpell is not creating `.local/share/juju-spell`
    # directory, so we need to create it
    lxd_execute(client, ["mkdir", "-p", str(DEFAULT_DIRECTORY)])

    return client


def boostrap_controller(name: str, series: str, ssh_key: str) -> Instance:
    """Bootstrap controller on top of instance."""
    # NOTE (rgildein): we could not use f"--config authorized-keys='{ssh_key}'",
    # because it's not appending key and Juju will not have access to this controller
    subprocess.check_output(
        [
            "juju",
            "bootstrap",
            "--no-switch",
            "--bootstrap-series",
            f"{series}",
            "--config",
            f"api-port={CONTROLLER_API_PORT}",
            "--config",
            f"default-series={series}",
            "localhost",
            name,
        ]
    )
    info = subprocess.check_output(["juju", "show-controller", name, "--format", "json"]).decode()
    info = json.loads(info)
    instance_id = info[name]["controller-machines"]["0"]["instance-id"]
    client = Client()
    # ranme controller container so we can easily access it a remove it later
    controller = client.instances.get(instance_id)
    lxd_execute(controller, ["sh", "-c", f"echo '{ssh_key}'>>/home/ubuntu/.ssh/authorized_keys"])
    controller.stop(wait=True)
    controller.rename(name, wait=True)
    controller.start(wait=True)
    return controller


def setup_environment(
    session_uuid: str, series: str, snap_path: Union[str, Path]
) -> Tuple[str, List[str]]:
    """Set up LXD environment.

    Creates client with JujuSpell installed and NUMBER_OF_CONTROLLERS for testing.
    """
    # JujuSpell client
    client = create_client_instance(session_uuid, series, snap_path)  # JujuSpell client
    client_ssh_key = lxd_execute(client, ["cat", "/home/ubuntu/.ssh/id_rsa.pub"]).stdout.strip()
    # Note(rgildein): Right now our connection could not accept ssh key
    # automaticaly, that's why we need to do this
    client.files.put("/home/ubuntu/.ssh/config", SSH_CONFIG, uid=1000)

    # controllers
    controllers = []
    for i in range(NUMBER_OF_CONTROLLERS):
        name = f"{CONTAINER_PREFIX}-controller-{i}-{session_uuid}"
        controller = boostrap_controller(name, series, client_ssh_key)
        controllers.append(controller.name)

    # creates JujuSpell config
    config = {"controllers": []}
    for controller in controllers:
        info = convert_config(get_controller(controller))
        ip_address, _ = info["endpoint"].split(":")
        config["controllers"].append(
            {
                "owner": "Frodo",
                "customer": "Gandalf",
                **info,
                "connection": {"destination": ip_address},
            }
        )
    config_string = yaml.safe_dump(config)
    client.files.put(DEFAULT_DIRECTORY / "config.yaml", config_string, uid=1000, gid=1000)

    return client.name, controllers


def cleanup_environment(session_uuid: str, keep_env: bool = False):
    """Clean up LXD environment.

    Remove all instances with names starting with CONTAINER_PREFIX.
    """
    client = Client()
    for instance in client.instances.all():
        if str(session_uuid) in instance.name:
            if keep_env:
                # check if instance is not already stopped
                if instance.status_code != STOPPED_CONTAINER_CODE:
                    instance.stop(wait=True)

                instance.delete()
                print(f"LXD: {instance.name} was removed")
                try_unregister_controller(instance.name)
            else:
                print(f"LXD: {instance.name} was kept for further testing")
