"""Configuration loader."""
import dataclasses
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import confuse
import yaml
from confuse import ConfigError, RootView

from juju_spell.exceptions import JujuSpellError
from juju_spell.settings import (
    DEFAULT_CONNECTIN_TIMEOUT,
    DEFAULT_CONNECTIN_WAIT,
    DEFAULT_PORT_RANGE,
)
from juju_spell.utils import merge_list_of_dict_by_key

logger = logging.getLogger(__name__)

ENDPOINT_REGEX = (
    r"^(?:http)s?://"  # http:// or https://
    # host
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
    r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(?::\d+)?"  # Optional[port]
    r"(?:/?|[/?]\S+)$"
)
API_ENDPOINT_REGEX = (
    # host
    r"^(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
    r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
    r"(:\d+)?$"  # port
)
UUID_REGEX = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
CA_CERT_REGEX = r"^(-*)BEGIN CERTIFICATE(-*)\n((.|\n)*)\n(-*)END CERTIFICATE(-*)$"
SUBNET_REGEX = r"^([0-9]{1,3}\.){3}[0-9]{1,3}($|/(8|9|1[0-9]|2[0-9]|3[0-2]))$"
DESTINATION_REGEX = (
    r"^([A-Za-z]*@)?"  # Optional[user]
    # host
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    r"([A-Za-z0-9,_,\-,.]*)|"  # destination
    r"localhost|"  # localhost
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$"  # IP
)
PORT_RANGE = (
    r"^((6553[0-5])|(655[0-2][0-9])|(65[0-4][0-9]{2})|"
    r"(6[0-4][0-9]{3})|([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4}))"
    r":"  # delimiter
    r"((6553[0-5])|(655[0-2][0-9])|(65[0-4][0-9]{2})|(6[0-4][0-9]{3})|"
    r"([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4}))$"
)


class String(confuse.Template):
    """A template used to validate string with regex and provide custom error."""

    def __init__(self, pattern: str, message: str, default: Optional[str] = None):
        """Initialize the String object."""
        super(String, self).__init__(default=default)
        self._regex = re.compile(pattern)
        self._message = message

    def convert(self, value: Any, view: confuse.ConfigView) -> str:
        """Check that the value is valid url."""
        if isinstance(value, str) and re.match(self._regex, value) is not None:
            return value

        self.fail(self._message, view, True)


class PortRange(String):
    """A template specific for port range."""

    def convert(self, value: Any, view: confuse.ConfigView) -> range:
        """Check and convert port_range string to tuple."""
        value = super().convert(value, view)
        start_port, end_port = value.split(":")
        return range(int(start_port), int(end_port))


class ControllerDict(confuse.MappingTemplate):
    """Controller template."""

    def value(self, view, template=None):
        """Get Controller object from dict."""
        output = super().value(view, template)
        return Controller(**output)


class ConnectionDict(confuse.MappingTemplate):
    """Connection template."""

    def value(self, view, template=None):
        """Get Connection object from dict."""
        output = super().value(view, template)
        return Connection(**output)


class RetryPolicyDict(confuse.MappingTemplate):
    def value(self, view, template=None):
        """Get RetryPolicy object from dict."""
        output = super().value(view, template)
        return RetryPolicy(**output)


DEFAULT_KEY = "default"
JUJUSPELL_CONTROLLER_TEMPLATE = ControllerDict(
    {
        "uuid": String(UUID_REGEX, "Invalid uuid definition"),
        "name": str,
        "customer": str,
        "owner": str,
        "description": confuse.Optional(str),
        "tags": confuse.Optional(confuse.Sequence(str)),
        "risk": confuse.Choice(range(1, 6), default=5),
        "endpoint": String(API_ENDPOINT_REGEX, "Invalid api endpoint definition"),
        "ca_cert": String(CA_CERT_REGEX, "Invalid ca-cert format"),
        "user": str,
        "password": str,
        "model_mapping": confuse.MappingTemplate(
            {
                "lma": confuse.Optional(confuse.Sequence(str)),
                "default": confuse.Optional(confuse.Sequence(str)),
            }
        ),
        "connection": confuse.Optional(
            ConnectionDict(
                {
                    "subnets": confuse.Optional(
                        confuse.Sequence(
                            String(SUBNET_REGEX, "Invalid subnet definition")
                        )
                    ),
                    "destination": String(
                        DESTINATION_REGEX, "Invalid destination definition"
                    ),
                    "jumps": confuse.Optional(
                        confuse.Sequence(
                            String(DESTINATION_REGEX, "Invalid jump definition")
                        )
                    ),
                    "port_range": confuse.Optional(
                        PortRange(
                            PORT_RANGE,
                            "Invalid port_range definition",
                        ),
                        default=DEFAULT_PORT_RANGE,
                    ),
                }
            )
        ),
        "retry_policy": confuse.Optional(
            RetryPolicyDict(
                {
                    "timeout": confuse.Optional(int),
                    "attempt": confuse.Optional(int),
                    "wait": confuse.Optional(int),
                }
            )
        ),
    }
)


JUJU_DEFAULT_CONTROLLER_DICT = {
    "uuid": confuse.Optional(String(UUID_REGEX, "Invalid uuid definition")),
    "name": confuse.Optional(str),
    "customer": confuse.Optional(str),
    "owner": confuse.Optional(str),
    "description": confuse.Optional(str),
    "tags": confuse.Optional(confuse.Sequence(str)),
    "risk": confuse.Optional(confuse.Choice(range(1, 6), default=5)),
    "endpoint": confuse.Optional(
        String(
            API_ENDPOINT_REGEX,
            "Invalid api endpoint definition",
        )
    ),
    "ca_cert": confuse.Optional(String(CA_CERT_REGEX, "Invalid ca-cert format")),
    "user": confuse.Optional(str),
    "password": confuse.Optional(str),
    "model_mapping": confuse.Optional(
        confuse.MappingTemplate(
            {
                "lma": confuse.Optional(confuse.Sequence(str)),
                "default": confuse.Optional(confuse.Sequence(str)),
            }
        )
    ),
    "connection": confuse.Optional(
        ConnectionDict(
            {
                "subnets": confuse.Optional(
                    confuse.Sequence(
                        String(
                            SUBNET_REGEX,
                            "Invalid subnet definition",
                        )
                    )
                ),
                "destination": confuse.Optional(
                    String(
                        DESTINATION_REGEX,
                        "Invalid destination definition",
                    )
                ),
                "jumps": confuse.Optional(
                    confuse.Sequence(
                        String(
                            DESTINATION_REGEX,
                            "Invalid jump definition",
                        )
                    )
                ),
                "port_range": confuse.Optional(
                    PortRange(
                        PORT_RANGE,
                        "Invalid port_range definition",
                    ),
                    default=DEFAULT_PORT_RANGE,
                ),
            }
        )
    ),
    "retry_policy": confuse.Optional(
        RetryPolicyDict(
            {
                "timeout": confuse.Optional(int),
                "attempt": confuse.Optional(int),
                "wait": confuse.Optional(int),
            }
        )
    ),
}

JUJUSPELL_DEFAULT_CONFIG_TEMPLATE = confuse.MappingTemplate(
    {
        DEFAULT_KEY: confuse.MappingTemplate(
            {
                "controller": confuse.Optional(
                    # Should not have uuid and name
                    confuse.MappingTemplate(JUJU_DEFAULT_CONTROLLER_DICT)
                ),
            }
        ),
        "controllers": confuse.Optional(
            confuse.Sequence(
                # uuid and name are required, else is optional
                confuse.MappingTemplate(JUJU_DEFAULT_CONTROLLER_DICT)
            )
        ),
    }
)

JUJUSPELL_CONFIG_TEMPLATE = confuse.MappingTemplate(
    {
        "controllers": confuse.Sequence(JUJUSPELL_CONTROLLER_TEMPLATE),
    }
)


@dataclasses.dataclass
class RetryPolicy:
    """ConnectionManager retry policy."""

    attempt: Optional[int] = 3
    wait: Optional[int] = DEFAULT_CONNECTIN_WAIT
    timeout: Optional[int] = DEFAULT_CONNECTIN_TIMEOUT


@dataclasses.dataclass
class Connection:
    destination: str
    jumps: Optional[List[str]] = None
    subnets: Optional[List[str]] = None
    port_range: Optional[range] = DEFAULT_PORT_RANGE


@dataclasses.dataclass
class Controller:
    """Juju Controller."""

    uuid: uuid.UUID
    name: str
    customer: str
    owner: str
    endpoint: str
    ca_cert: str
    user: str
    password: str
    model_mapping: Dict[str, List[str]]
    # optional attributes and attributes with default value
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    risk: int = 5
    connection: Optional[Connection] = None
    retry_policy: Optional[RetryPolicy] = None


@dataclasses.dataclass
class Config:
    controllers: List[Controller]


def validate_source_match_template(
    source: Dict[str, Any],
    template: confuse.MappingTemplate,
) -> Config:
    """Return valid config if source match template, else raise ConfigError."""
    try:
        _config = RootView([source])
        valid_config = _config.get(template)
        return valid_config
    except ConfigError as error:
        logger.error("configuration file validation failed with error: %s", error)
        raise JujuSpellError("configuration file validation failed") from error


def _validate_config(source: Dict[str, Any]) -> Config:
    """Validate config.

    Using confuse library to validate config.
    """
    valid_config = validate_source_match_template(source, JUJUSPELL_CONFIG_TEMPLATE)
    return Config(**valid_config)


def _apply_default_dict(source: Dict[Any, Any], default: Dict[Any, Any]):
    new_dict = source.copy()
    for k in default:
        target_val = source.get(k, default.get(k))
        if isinstance(target_val, dict):
            new_dict[k] = _apply_default_dict(target_val, default[k])
        elif isinstance(target_val, list):
            new_dict[k] = _apply_default_list(target_val, default[k])
        else:
            new_dict[k] = target_val
    return new_dict


def _apply_default_list(source: List[Any], default):
    new_list = []
    for value in source:
        if isinstance(value, dict) and isinstance(default, dict):
            new_list.append(_apply_default_dict(value, default))
        else:
            new_list.append(default)
    return new_list


def _apply_default(source: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default value to every elements in list.

    If the config look like this:

    ```yaml
    default:
        controller: {"password": "pwd"}
    controllers:
      - name: abc
        ...
      - name: cbd
        ...
    ```
    The values in default.controller will be apply to every elements in controllers
    if the value is not exists.
    """
    validate_source_match_template(source, JUJUSPELL_DEFAULT_CONFIG_TEMPLATE)

    default = source.pop(DEFAULT_KEY, None)
    if default is None:
        return source

    for key, value in default.items():
        target_key = key + "s"
        # List of dict
        if isinstance(source.get(target_key), list):
            source[target_key] = _apply_default_list(source[target_key], value)
        if isinstance(source.get(target_key), dict):
            source[target_key] = _apply_default_dict(source[target_key], value)
    return source


def merge_configs(config: Dict, personal_config: Dict):
    """Merge personal and global config."""
    # Merge default
    config_defualt = config.get(DEFAULT_KEY, {})
    personal_defualt = personal_config.get(DEFAULT_KEY, {})

    # Get set of all keys in default
    default_keys = set().union(*[config_defualt, personal_defualt])
    for key in default_keys:
        config[DEFAULT_KEY][key] = {
            **config_defualt.get(key, {}),
            **personal_defualt.get(key, {}),
        }

    # Merge controllers by unique key uuid
    if config.get("controllers") and personal_config.get("controllers"):
        config["controllers"] = merge_list_of_dict_by_key(
            key="uuid",
            lists=[config["controllers"], personal_config["controllers"]],
        )
    return config


def load_config_file(path):
    """Load config file.

    raises: IsADirectoryError if path is directory
    raises: FileNotFoundError -> JujuSpellError if fies does not exist
    raises: PermissionError -> JujuSpellError if user has no permission to path
    """
    try:
        with open(path, "r") as file:
            source = yaml.safe_load(file)
            logger.info("load config file from %s path", path)
            return source
    except FileNotFoundError as error:
        logger.error("config file `%s` does not exists", path)
        raise JujuSpellError(f"config file {path} does not exist") from error
    except PermissionError as error:
        logger.error("not enough permission for configuration file `%s`", path)
        raise JujuSpellError(f"permission denied to read config file {path}") from error
    except ConfigError as error:
        logger.error("configuration file validation failed with error: %s", error)
        raise JujuSpellError("configuration file validation failed") from error


def load_config(
    config_path: Path, personal_config_path: Optional[Path] = None
) -> Config:
    """Load ad validate yaml config file."""
    source = load_config_file(config_path)
    if personal_config_path and personal_config_path.exists():
        personal_source = load_config_file(personal_config_path)
        # Merge personal and default config
        source = merge_configs(source, personal_source)

    source = _apply_default(source)
    config = _validate_config(source)
    return config


def convert_config(original_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Juju config from `juju show-controller` to JujuSpell config.

    Returns first object of dictionary, because format of output is defined as
    a dictionary where key is name of controller.
    """
    for name, controller in original_config.items():
        config = {
            "uuid": controller["details"]["uuid"],
            "name": name,
            "endpoint": controller["details"]["api-endpoints"][0],
            "ca_cert": controller["details"]["ca-cert"],
            "user": controller["account"]["user"],
            "password": controller["account"]["password"],
        }
        return config
