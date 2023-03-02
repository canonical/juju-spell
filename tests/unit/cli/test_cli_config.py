import argparse
import io
from typing import List
from unittest import mock

import pytest as pytest
import yaml

from juju_spell.cli.config import ConfigCMD, KeyValue, get_application_config
from juju_spell.commands.config import ApplicationConfig

TEST_APPLICATION_YAML = """
squid-reverseproxy:
  cache_size_mb: "129"
  cache_mem_mb: "257"
ubuntu:
  hostname: test-test
"""

TEST_APPLICATION_CONFIG = [
    ApplicationConfig(
        application="squid-reverseproxy", config={"cache_size_mb": "129", "cache_mem_mb": "257"}
    ),
    ApplicationConfig(application="ubuntu", config={"hostname": "test-test"}),
]


def test_fill_parser():
    """Test add additional CLI arguments with ConfigCMD."""
    parser = mock.MagicMock(spec=argparse.ArgumentParser)

    cmd = ConfigCMD(None)
    cmd.fill_parser(parser)

    # This one is to check the basic arguments is been added.
    assert parser.add_argument.call_count == 7
    assert parser.add_mutually_exclusive_group.call_count == 1
    parser.add_argument.assert_has_calls(
        [
            mock.call("--config-get", type=str, help="Single property to get.", required=False),
            mock.call(
                "--config-set",
                nargs="*",
                help="key=value pairs to update application config.",
                required=False,
                action=KeyValue,
            ),
        ]
    )


@pytest.mark.parametrize("input_yaml", [TEST_APPLICATION_YAML])
@mock.patch("juju_spell.utils.load_yaml_file")
def test_get_application_config(mock_load_patch_file, input_yaml):
    mock_load_patch_file.return_value = yaml.safe_load(io.StringIO(input_yaml))
    real: List[ApplicationConfig] = get_application_config("test")
    assert real == TEST_APPLICATION_CONFIG
    mock_load_patch_file.assert_called_once_with("test")


#
# mock.call("--file", type=get_application_config,
#           help="The path to yaml-formatted application config.", required=False),
# mock.call("--application", type=str, help="The application to show/update configuration.",
#           required=False),
