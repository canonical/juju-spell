import copy
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from juju_spell.cli.update_packages import get_patch_config
from juju_spell.commands.update_packages import (
    PackageUpdateResult,
    UnitUpdateResult,
    UpdatePackages,
    UpdateResult,
)

TEST_PATCH = """
---
applications:
- application: "^.*ubuntu.*$"
  dist_upgrade: True
  packages_to_update:
  - app: apt
    version: 2.4.8
  - app: rsync
    version: 3.2.3-8ubuntu3.1
"""

RAW_OUTPUT_DRYRUN = """
Hit:1 http://nova.clouds.archive.ubuntu.com/ubuntu jammy InRelease
Hit:2 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:3 http://security.ubuntu.com/ubuntu jammy-security InRelease
Hit:4 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-backports InRelease
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  apt-utils libapt-pkg6.0
Suggested packages:
  apt-doc aptitude | synaptic | wajig
The following packages will be upgraded:
  apt apt-utils libapt-pkg6.0 rsync
4 upgraded, 0 newly installed, 0 to remove and 50 not upgraded.
Inst libapt-pkg6.0 [2.4.7] (2.4.8 Ubuntu:22.04/jammy-updates [amd64])
Conf libapt-pkg6.0 (2.4.8 Ubuntu:22.04/jammy-updates [amd64])
Inst apt [2.4.7] (2.4.8 Ubuntu:22.04/jammy-updates [amd64]) [apt-utils:amd64 ]
Conf apt (2.4.8 Ubuntu:22.04/jammy-updates [amd64]) [apt-utils:amd64 ]
Inst apt-utils [2.4.7] (2.4.8 Ubuntu:22.04/jammy-updates [amd64])
Inst rsync [3.2.3-8ubuntu3] (3.2.3-8ubuntu3.1 Ubuntu:22.04/jammy-updates [amd64])
Conf apt-utils (2.4.8 Ubuntu:22.04/jammy-updates [amd64])
Conf rsync (3.2.3-8ubuntu3.1 Ubuntu:22.04/jammy-updates [amd64])
"""

RAW_OUTPUT_INSTALL = """# noqa
Hit:1 http://nova.clouds.archive.ubuntu.com/ubuntu jammy InRelease
Hit:2 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates InRelease
Hit:3 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-backports InRelease
Hit:4 http://security.ubuntu.com/ubuntu jammy-security InRelease
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  apt-utils libapt-pkg6.0
Suggested packages:
  apt-doc aptitude | synaptic | wajig
The following packages will be upgraded:
  apt apt-utils libapt-pkg6.0 rsync
4 upgraded, 0 newly installed, 0 to remove and 50 not upgraded.
Need to get 2900 kB of archives.
After this operation, 4096 B of additional disk space will be used.
Get:1 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates/main amd64 libapt-pkg6.0 amd64 2.4.8 [907 kB]
Get:2 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates/main amd64 apt amd64 2.4.8 [1379 kB]
Get:3 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates/main amd64 apt-utils amd64 2.4.8 [211 kB]
Get:4 http://nova.clouds.archive.ubuntu.com/ubuntu jammy-updates/main amd64 rsync amd64 3.2.3-8ubuntu3.1 [404 kB]
Fetched 2900 kB in 1s (3332 kB/s)
(Reading database ... 101588 files and directories currently installed.)
Preparing to unpack .../libapt-pkg6.0_2.4.8_amd64.deb ...
Unpacking libapt-pkg6.0:amd64 (2.4.8) over (2.4.7) ...
Setting up libapt-pkg6.0:amd64 (2.4.8) ...
(Reading database ... 101588 files and directories currently installed.)
Preparing to unpack .../archives/apt_2.4.8_amd64.deb ...
Unpacking apt (2.4.8) over (2.4.7) ...
Setting up apt (2.4.8) ...
(Reading database ... 101588 files and directories currently installed.)
Preparing to unpack .../apt-utils_2.4.8_amd64.deb ...
Unpacking apt-utils (2.4.8) over (2.4.7) ...
Preparing to unpack .../rsync_3.2.3-8ubuntu3.1_amd64.deb ...
Unpacking rsync (3.2.3-8ubuntu3.1) over (3.2.3-8ubuntu3) ...
Setting up apt-utils (2.4.8) ...
Setting up rsync (3.2.3-8ubuntu3.1) ...
rsync.service is a disabled or a static unit not running, not starting it.
Processing triggers for man-db (2.10.2-1) ...
Processing triggers for libc-bin (2.35-0ubuntu3.1) ...
Scanning processes...
Scanning candidates...
Scanning linux images...

Restarting services...
 /etc/needrestart/restart.d/systemd-manager
 systemctl restart cron.service packagekit.service polkit.service rsyslog.service ssh.service systemd-journald.service systemd-networkd.service systemd-resolved.service systemd-timesyncd.service systemd-udevd.service udisks2.service
Service restarts being deferred:
 systemctl restart ModemManager.service
 /etc/needrestart/restart.d/dbus.service
 systemctl restart networkd-dispatcher.service
 systemctl restart systemd-logind.service
 systemctl restart unattended-upgrades.service
 systemctl restart user@1000.service

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
"""

UNIT_UPDATE_COMMAND = (
    "sudo apt-get update ; sudo apt-get"
    " --option=Dpkg::Options::=--force-confold"
    " --option=Dpkg::Options::=--force-confdef dist-upgrade --upgrade -y  "
)


@pytest.fixture
def unit_update_result():
    return UnitUpdateResult(
        unit="ubuntu/0",
        command=UNIT_UPDATE_COMMAND,
        raw_output=RAW_OUTPUT_DRYRUN,
        success=True,
        packages=[
            PackageUpdateResult(
                package="apt",
                from_version="2.4.7",
                to_version="2.4.8",
            ),
            PackageUpdateResult(
                package="rsync",
                from_version="3.2.3-8ubuntu3",
                to_version="3.2.3-8ubuntu3.1",
            ),
        ],
    )


@pytest.fixture
def expected_packages(patch_config):
    return patch_config.applications[0].packages_to_update


@pytest.fixture(params=[TEST_PATCH])
def patch_config(request, tmp_path):
    """Test get_patch_config."""
    file_path = tmp_path / f"{uuid.uuid4()}.config"
    with open(file_path, "w", encoding="utf8") as file:
        file.write(request.param)

    return get_patch_config(file_path)


async def _mock_controller(model):
    controller = AsyncMock()
    controller.get_model.return_value = model
    controller_config = AsyncMock()
    controller_config.model_mapping = None
    return controller, controller_config


async def _mock_model(output):
    model = AsyncMock()
    unit = AsyncMock()
    unit.name = "ubuntu/0"
    action = MagicMock()
    action.data = {"results": {"Stdout": output}}
    unit.run.return_value = action
    model.units = {"ubuntu/0": unit}
    app_status = AsyncMock()
    app_status.units = [unit]
    model.applications = {"ubuntu": app_status}
    return model


def test_set_success_flags(unit_update_result, expected_packages):
    update_packages: UpdatePackages = UpdatePackages()
    update_packages.set_success_flags(unit_update_result, expected_packages)
    assert unit_update_result.success


def test_set_apps_to_update(patch_config, unit_update_result):
    result = copy.deepcopy(patch_config)
    model = AsyncMock()
    app_status = AsyncMock()
    unit = AsyncMock()
    unit.name = "ubuntu/0"
    app_status.units = [unit]
    model.applications = {"ubuntu": app_status}

    update_packages: UpdatePackages = UpdatePackages()
    update_packages.set_apps_to_update(updates=patch_config, model=model, dry_run=False)

    unit_update_result = copy.deepcopy(unit_update_result)
    unit_update_result.packages = None
    update_result = copy.deepcopy(unit_update_result)
    update_result.raw_output = ""
    update_result.success = False
    result.applications[0].results = [
        UpdateResult(application="ubuntu", units=[update_result])
    ]

    assert result == patch_config


def test_get_update_command(patch_config):
    update_packages: UpdatePackages = UpdatePackages()

    app = patch_config.applications[0]
    res = update_packages.get_update_command(app, False)
    assert (
        res
        == "sudo apt-get update ; sudo apt-get --option=Dpkg::Options::=--force-confold"
        " --option=Dpkg::Options::=--force-confdef dist-upgrade --upgrade -y  "
    )
    res = update_packages.get_update_command(app, True)
    assert (
        res
        == "sudo apt-get update ; sudo apt-get --option=Dpkg::Options::=--force-confold"
        " --option=Dpkg::Options::=--force-confdef dist-upgrade --upgrade -y "
        " --dry-run"
    )
    app.dist_upgrade = False
    res = update_packages.get_update_command(app, False)
    assert (
        res
        == "sudo apt-get update ; sudo apt-get --option=Dpkg::Options::=--force-confold"
        " --option=Dpkg::Options::=--force-confdef install --upgrade -y apt rsync "
    )
    res = update_packages.get_update_command(app, True)
    assert (
        res
        == "sudo apt-get update ; sudo apt-get --option=Dpkg::Options::=--force-confold"
        " --option=Dpkg::Options::=--force-confdef install --upgrade -y apt"
        " rsync --dry-run"
    )


def test_parse_result(unit_update_result):
    update_packages: UpdatePackages = UpdatePackages()
    result = update_packages.parse_result(RAW_OUTPUT_INSTALL)
    assert [p in result for p in unit_update_result.packages] == [True, True]

    result = update_packages.parse_result(RAW_OUTPUT_DRYRUN)
    assert [p in result for p in unit_update_result.packages] == [True, True]


@pytest.mark.asyncio
async def test_run_updates_on_model(patch_config, unit_update_result):
    update_packages: UpdatePackages = UpdatePackages()
    model = await _mock_model(RAW_OUTPUT_DRYRUN)

    patch_config.applications[0].results = [
        UpdateResult(
            application="ubuntu",
            units=[
                UnitUpdateResult(
                    unit="ubuntu/0",
                    command=UNIT_UPDATE_COMMAND,
                    success=False,
                    raw_output=RAW_OUTPUT_DRYRUN,
                )
            ],
        )
    ]

    await update_packages.run_updates_on_model(model=model, updates=patch_config)
    assert [
        p in patch_config.applications[0].results[0].units[0].packages
        for p in unit_update_result.packages
    ] == [True, True]


@pytest.mark.asyncio
async def test_make_updates(patch_config, unit_update_result):
    model = await _mock_model(RAW_OUTPUT_DRYRUN)

    controller = AsyncMock()
    controller.get_model.return_value = model

    update_packages: UpdatePackages = UpdatePackages()
    result = await update_packages.make_updates(
        controller=controller,
        updates=patch_config,
        models=["lma"],
        model_mapping=None,
        dry_run=False,
    )

    assert result.success
    assert [
        p in result.output["lma"].applications[0].results[0].units[0].packages
        for p in unit_update_result.packages
    ] == [True, True]


@pytest.mark.asyncio
async def test_execute(patch_config, unit_update_result):
    model = await _mock_model(RAW_OUTPUT_DRYRUN)
    controller, controller_config = await _mock_controller(model)

    update_packages: UpdatePackages = UpdatePackages()
    result = await update_packages.execute(
        controller=controller,
        models=["lma"],
        **{
            "controller_config": controller_config,
            "patch": patch_config,
            "dry_run": False,
        },
    )
    assert result.success
    assert [
        p in result.output["lma"].applications[0].results[0].units[0].packages
        for p in unit_update_result.packages
    ] == [True, True]


@pytest.mark.asyncio
async def test_dry_run(patch_config, unit_update_result):
    model = await _mock_model(RAW_OUTPUT_DRYRUN)
    controller, controller_config = await _mock_controller(model)

    update_packages: UpdatePackages = UpdatePackages()
    result = await update_packages.dry_run(
        controller=controller,
        models=["lma"],
        **{
            "controller_config": controller_config,
            "patch": patch_config,
            "dry_run": True,
        },
    )
    assert result.success
    assert [
        p in result.output["lma"].applications[0].results[0].units[0].packages
        for p in unit_update_result.packages
    ] == [True, True]
