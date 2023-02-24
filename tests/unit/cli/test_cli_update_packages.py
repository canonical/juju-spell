import argparse
import io
import uuid
from unittest import mock

import pytest
import yaml

from juju_spell.cli import UpdatePackages
from juju_spell.cli.update_packages import get_patch_config, load_patch_file
from juju_spell.commands.update_packages import Application, PackageToUpdate, Updates

TEST_PATCH = """
---
applications:
- application: "^.*ubuntu.*$"
  dist_upgrade: True
  packages_to_update:
  - app: nova-common
    version: 2:21.2.4-0ubuntu2.1
  - app: python3-nova
    version: 2:21.2.4-0ubuntu2.1
"""

TEST_UPDATES = Updates(
    [
        Application(
            name_expr="^.*ubuntu.*$",
            dist_upgrade=True,
            results=[],
            packages_to_update=[
                PackageToUpdate(package="nova-common", version="2:21.2.4-0ubuntu2.1"),
                PackageToUpdate(package="python3-nova", version="2:21.2.4-0ubuntu2.1"),
            ],
        )
    ]
)


def test_fill_parser():
    """Test add additional CLI arguments with BaseJujuCMD."""
    parser = mock.MagicMock(spec=argparse.ArgumentParser)

    cmd = UpdatePackages(None)
    cmd.fill_parser(parser)

    # This one is to check the basic arguments is been added.
    assert parser.add_argument.call_count == 6
    parser.add_argument.assert_has_calls(
        [
            mock.call(
                "--patch", type=get_patch_config, help="patch file", required=True
            ),
        ]
    )


@pytest.mark.parametrize("input_yaml", [TEST_PATCH])
def test_load_patch_file(tmp_path, input_yaml):
    """Test load_patch_file."""
    file_path = tmp_path / f"{uuid.uuid4()}.yaml"
    with open(file_path, "w", encoding="utf8") as file:
        file.write(input_yaml)

    result = load_patch_file(file_path)
    assert result == yaml.safe_load(io.StringIO(input_yaml))


@pytest.mark.parametrize("input_yaml", [TEST_PATCH])
@mock.patch("juju_spell.cli.update_packages.load_patch_file")
def test_get_patch_config(mock_load_patch_file, input_yaml):
    """Test get_patch_config."""
    mock_load_patch_file.return_value = yaml.safe_load(io.StringIO(input_yaml))

    real: Updates = get_patch_config(file_path="test")
    assert real == TEST_UPDATES
    mock_load_patch_file.assert_called_once_with("test")
