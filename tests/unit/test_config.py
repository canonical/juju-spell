import io
import uuid
from typing import Any, Dict
from unittest import mock

import pytest
import yaml
from confuse import ConfigTypeError, ConfigView, MappingTemplate

from juju_spell.config import (
    API_ENDPOINT_REGEX,
    DESTINATION_REGEX,
    SUBNET_REGEX,
    UUID_REGEX,
    Config,
    String,
    _apply_default,
    _validate_config,
    load_config,
    load_config_file,
    merge_configs,
    validate_source_match_template,
)
from juju_spell.exceptions import JujuSpellError
from tests.unit.conftest import TEST_CONFIG, TEST_PERSONAL_CONFIG


@pytest.mark.parametrize(
    "regex, value",
    [
        (r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", "1.2.3.4"),
        (SUBNET_REGEX, "1.2.3.0/24"),
        (UUID_REGEX, "e53042ba-8ff5-456c-85b8-f7fef37bff5c"),
        (DESTINATION_REGEX, "maas3.frodo-baggins.mordor"),
        (API_ENDPOINT_REGEX, "10.1.1.177:17070"),  # test IPV4 endpoint
    ],
)
def test_string(regex, value):
    """Test custom string option."""
    string = String(regex, "test message")
    view = ConfigView()
    assert string.convert(value, view) == value


@pytest.mark.parametrize(
    "regex, value", [(SUBNET_REGEX, "1.2"), (UUID_REGEX, "1-2-3-4-5")]
)
def test_string_exception(regex, value):
    """Test custom string option."""
    string = String(regex, "test message")
    view = ConfigView()
    with pytest.raises(ConfigTypeError):
        string.convert(value, view)


def _update_test_config(
    config: Dict[str, Any], extra_configuration: Dict[str, Any]
) -> Dict[str, Any]:
    """Update test config."""
    updated_config = config.copy()
    extra_connection_configuration = extra_configuration.get("connection", {})
    extra_controller_configuration = extra_configuration.get("controllers", [])

    for key, value in extra_connection_configuration.items():
        if "connection" not in updated_config:
            updated_config["connection"] = {}

        updated_config["connection"][key] = value

    for i, controller in enumerate(extra_controller_configuration):
        if "controllers" not in updated_config:
            updated_config["controllers"] = []

        for key, value in controller.items():
            updated_config["controllers"][i][key] = value

    return updated_config


@pytest.mark.parametrize(
    "extra_configuration, exp_connection, exp_controller",
    [
        (
            {},  # extra configuration
            {},  # connection
            [
                {
                    "name": "example_controller",
                    "endpoint": "10.1.1.46:17070",
                },  # controller 0
                {
                    "name": "example_controller_without_optional",
                    "endpoint": "10.1.1.47:17070",
                },  # controller 1
            ],
        ),
        # test optional configuration option
        (
            {},  # extra configuration
            {"port-range": range(17071, 17170)},  # connection
            [
                {
                    "description": "some nice notes",
                    "tags": ["test"],
                    "risk": 3,
                },  # controller 0
                {
                    "description": None,
                    "tags": None,
                    "risk": 5,
                    "connection": None,
                },  # controller 1
            ],
        ),
        (
            {"connection": {"port-range": "18000:1900"}},  # extra configuration
            {"port-range": range(18000, 1900)},  # connection
            [
                {
                    "name": "example_controller",
                    "endpoint": "10.1.1.46:17070",
                },  # controller 0
                {
                    "name": "example_controller_without_optional",
                    "endpoint": "10.1.1.47:17070",
                },  # controller 1
            ],
        ),
        # test empty model in model_mapping
        (
            {  # extra configuration
                "controllers": [
                    {
                        "model_mapping": {
                            "lma": None,
                            "default": None,
                        }
                    }
                ]
            },
            {},  # connection
            [
                {
                    "name": "example_controller",
                    "endpoint": "10.1.1.46:17070",
                    "model_mapping": {
                        "lma": None,
                        "default": None,
                    },
                },  # controller 0
                {
                    "name": "example_controller_without_optional",
                    "endpoint": "10.1.1.47:17070",
                },  # controller 1
            ],
        ),
        # test special destination
    ],
)
def test_validate_config(
    extra_configuration, exp_connection, exp_controller, test_config_dict
):
    """Test validate config."""
    test_config = _update_test_config(test_config_dict, extra_configuration)

    config = _validate_config(test_config)

    assert isinstance(config, Config)

    # check connections
    for key, value in exp_connection.items():
        assert getattr(config.connection, key) == value

    # check controllers
    for i, controller in enumerate(exp_controller):
        for key, value in controller.items():
            assert getattr(config.controllers[i], key) == value


@pytest.mark.parametrize(
    "extra_configuration",
    [
        {"connection": {"port-range": "17070"}},
        {"connection": {"port-range": "1:100000"}},
        {"controllers": [{"name": 1}]},
        {"controllers": [{"customer": None}]},
        {"controllers": [{"owner": None}]},
        {"controllers": [{"tags": {"test": 1}}]},
        {"controllers": [{"risk": 6}]},
        {"controllers": [{"endpoint": "1.2.3"}]},
        {"controllers": [{"endpoint": "llocalhost"}]},
        {"controllers": [{"ca_cert": "1234"}]},
        {
            "controllers": [
                {"connection": {"destination": "1.2.3.4", "subnets": ["1.2.3.4/00"]}}
            ]
        },
        {
            "controllers": [
                {"connection": {"destination": "1.2.3.4", "subnets": ["1.2"]}}
            ]
        },
        {"controllers": [{"connection": {"destination": "1.2.3.4", "jumps": [None]}}]},
    ],
)
def test_validate_config_failure(extra_configuration, test_config_dict):
    """Test failure of config validation."""
    test_config = _update_test_config(test_config_dict, extra_configuration)

    with pytest.raises(Exception):
        _validate_config(test_config)


@pytest.mark.parametrize(
    "config,personal_config,result",
    [
        (
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user1",
                    },
                ],
            },
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user2",
                    },
                ],
            },
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user2",
                    },
                ],
            },
        ),
        (
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user1",
                    },
                    {
                        "uuid": "723ff799-d50d-4a6f-b332-21954b86e422",
                        "username": "user3",
                    },
                ],
            },
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user2",
                    },
                ],
            },
            {
                "controllers": [
                    {
                        "uuid": "4f9988ff-3ff3-4644-9727-c47bb2d99588",
                        "username": "user2",
                    },
                    {
                        "uuid": "723ff799-d50d-4a6f-b332-21954b86e422",
                        "username": "user3",
                    },
                ],
            },
        ),
        (
            {"default": {"controller": {"name": "abc"}}},
            {"default": {"controller": {"name": "bcd"}}},
            {"default": {"controller": {"name": "bcd"}}},
        ),
        (
            {"default": {"controller": {"name": "abc", "user": "admin"}}},
            {"default": {"controller": {"name": "bcd"}}},
            {"default": {"controller": {"name": "bcd", "user": "admin"}}},
        ),
    ],
)
def test_merge_configs(config, personal_config, result):
    """Test merge_configs."""
    new_config = merge_configs(config, personal_config)
    assert new_config == result


@pytest.mark.parametrize("config_yaml", [TEST_CONFIG, TEST_PERSONAL_CONFIG])
def test_load_config_file(tmp_path, config_yaml):
    """Test load_config_file."""
    file_path = tmp_path / f"{uuid.uuid4()}.config"
    with open(file_path, "w", encoding="utf8") as file:
        file.write(config_yaml)

    result = load_config_file(file_path)
    assert result == yaml.safe_load(io.StringIO(config_yaml))


@pytest.mark.parametrize(
    "raised_error, exp_error",
    [
        (FileNotFoundError, JujuSpellError),
        (PermissionError, JujuSpellError),
        (IsADirectoryError, IsADirectoryError),
    ],
)
@mock.patch("juju_spell.config.open")
def test_load_config_file_exception(mock_open, tmp_path, raised_error, exp_error):
    """Test raising JujuSpell exception."""
    mock_open.side_effect = raised_error
    with pytest.raises(exp_error):
        load_config_file(tmp_path)


@mock.patch("juju_spell.config._validate_config")
@mock.patch("juju_spell.config.merge_configs")
@mock.patch("juju_spell.config.load_config_file")
def test_load_config(
    mock_load_config_file, mock_merge_configs, mock_validate_config, tmp_path
):
    """Test load config."""
    test_config_path = tmp_path / "config.yaml"
    test_config_path.touch()
    test_personal_config_path = tmp_path / "config.personal.yaml"
    test_personal_config_path.touch()
    exp_config = {"test": 1}
    mock_load_config_file.return_value = exp_config

    # testing the load_config function
    config = load_config(test_config_path, test_personal_config_path)

    mock_load_config_file.assert_has_calls(
        [mock.call(test_config_path), mock.call(test_personal_config_path)]
    )
    mock_merge_configs.assert_called_once_with(exp_config, exp_config)
    mock_validate_config.assert_called_once_with(mock_merge_configs.return_value)
    assert config == mock_validate_config.return_value


@pytest.mark.parametrize(
    "source,exp",
    [
        # List of dict, merge
        (
            {"default": {"key_a": {"va": 1}}, "key_as": [{"vb": 2}]},
            {"key_as": [{"va": 1, "vb": 2}]},
        ),
        # List of dict, not overwrite
        (
            {"default": {"key_a": {"va": 1}}, "key_as": [{"va": 2, "vb": 2}]},
            {"key_as": [{"va": 2, "vb": 2}]},
        ),
        # List of dict, make sure apply default by key
        (
            {
                "default": {"key_a": {"va": 1}, "key_b": {"vb": 3}},
                "key_as": [{"va": 2, "vb": 2}],
            },
            {"key_as": [{"va": 2, "vb": 2}]},
        ),
        # List of dict, list of dict apply
        (
            {
                "default": {"key_a": {"va": 1}, "key_b": {"vb": 3}},
                "key_as": [{}, {}],
                "key_bs": [{}, {}],
            },
            {"key_as": [{"va": 1}, {"va": 1}], "key_bs": [{"vb": 3}, {"vb": 3}]},
        ),
        # List of nested dict
        (
            {
                "default": {"key_a": {"va": 1, "vb": {"vc": 1}}},
                "key_as": [{"vb": {"vd": 2}}],
            },
            {
                "key_as": [{"va": 1, "vb": {"vc": 1, "vd": 2}}],
            },
        ),
        # Simple Dict
        (
            {
                "default": {"key_a": {"va": 1}},
                "key_as": {},
            },
            {"key_as": {"va": 1}},
        ),
    ],
)
@mock.patch("juju_spell.config.validate_source_match_template")
def test__apply_default(_, source, exp):
    result = _apply_default(source)
    assert result == exp


@pytest.mark.parametrize(
    "template, source, exp_error",
    [
        (MappingTemplate({"a": str}), {"a": "a"}, None),
        (MappingTemplate({"a": str}), {"a": 1}, JujuSpellError),
    ],
)
def test_validate_source_match_template(template, source, exp_error):
    if exp_error:
        with pytest.raises(exp_error):
            validate_source_match_template(source, template)
    else:
        validate_source_match_template(source, template)
