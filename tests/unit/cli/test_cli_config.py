import argparse
import io
from pathlib import Path
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


def test_add_mutually_exclusive_group_parameters() -> None:
    application_group = mock.MagicMock(spec=argparse._MutuallyExclusiveGroup)
    cmd = ConfigCMD(None)
    cmd.add_mutually_exclusive_group_parameters(application_group)
    application_group.add_argument.assert_has_calls(
        [
            mock.call(
                "--config-file",
                type=get_application_config,
                required=False,
                help="The path to yaml-formatted application config.",
            ),
            mock.call(
                "--config-app",
                required=False,
                help="The application to show/update configuration.",
            ),
        ]
    )


@pytest.mark.parametrize("input_yaml", [TEST_APPLICATION_YAML])
@mock.patch("juju_spell.utils.load_yaml_file")
def test_get_application_config(mock_load_patch_file, input_yaml):
    mock_load_patch_file.return_value = yaml.safe_load(io.StringIO(input_yaml))
    real: List[ApplicationConfig] = get_application_config("test")
    assert real == TEST_APPLICATION_CONFIG
    mock_load_patch_file.assert_called_once_with(Path("test"))


@pytest.mark.parametrize(
    "parameters, expected",
    [
        (["--config-set", "a=3", "b=2", "c=z=2"], {"a": "3", "b": "2", "c": "z=2"}),
        (["--config-set", "x=3", "y=2"], {"x": "3", "y": "2"}),
        (["--config-set", 'x="2"', "y=2"], {"x": '"2"', "y": "2"}),
        (["--config-set", 'x="2=2"', "y=2"], {"x": '"2=2"', "y": "2"}),
    ],
)
def test_keyvalue(parameters, expected):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config-set",
        nargs="*",
        help="key=value pairs to update application config.",
        required=False,
        action=KeyValue,
    )
    args = parser.parse_args(args=parameters)
    assert args.config_set == expected
