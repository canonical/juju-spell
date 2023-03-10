import copy
from typing import Dict
from unittest.mock import AsyncMock

import pytest as pytest

from juju_spell.commands.config import (
    ApplicationConfig,
    ConfigCommand,
    apply_configuration,
    apply_file_config,
    values_only,
)

SIMPLE_CONFIG = {"hostname": "osman", "xx": "xx", "others": "xx"}
FULL_CONFIG = {
    "hostname": {
        "default": "",
        "description": "Override hostname, when empty uses default machine hostname",
        "source": "user",
        "type": "string",
        "value": "osman",
    },
    "xx": {
        "default": "",
        "description": "",
        "source": "user",
        "type": "string",
        "value": "xx",
    },
    "others": {
        "default": "",
        "description": "",
        "source": "user",
        "type": "string",
        "value": "xx",
    },
}


class MockApp:
    properties: Dict = {}

    def __init__(self):
        """Initialize with dictionary."""
        self.properties = copy.deepcopy(FULL_CONFIG)

    async def set_config(self, props: Dict[str, str]):
        for key, value in props.items():
            if key in self.properties.keys():
                self.properties[key]["value"] = value

    async def get_config(self):
        return self.properties


def _mock_model(mockapp: MockApp):
    model = AsyncMock()
    model.applications = {"ubuntu": mockapp}
    return model


def _mock_controller(model):
    controller = AsyncMock()
    controller.get_model.return_value = model
    controller_config = AsyncMock()
    controller_config.model_mapping = None
    return controller, controller_config


@pytest.mark.asyncio
async def test_execute_get_single_config():
    model = _mock_model(MockApp())
    controller, controller_config = _mock_controller(model)
    kwargs = {
        "config-app": "ubuntu",
        "config-get": "hostname",
        "controller_config": controller_config,
    }

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)
    assert result == {"lma": {"ubuntu": {"hostname": "osman"}}}


@pytest.mark.asyncio
async def test_execute_get_config():
    model = _mock_model(MockApp())
    controller, controller_config = _mock_controller(model)
    kwargs = {"config-app": "ubuntu", "controller_config": controller_config}

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)

    assert result == {"lma": {"ubuntu": SIMPLE_CONFIG}}


@pytest.mark.asyncio
async def test_execute_set_multiple_config():
    ubuntu_set_config = {"hostname": "xxx", "xx": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "xx": "44"}

    model = _mock_model(MockApp())
    controller, controller_config = _mock_controller(model)
    kwargs = {
        "config-app": "ubuntu",
        "controller_config": controller_config,
        "config_set": ubuntu_set_config,
    }

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)

    assert result == {"lma": {"ubuntu": ubuntu_expected_config}}


@pytest.mark.asyncio
async def test_execute_set_from_file():
    ubuntu_set_config = {"hostname": "xxx", "xx": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "xx": "44"}

    model = _mock_model(MockApp())
    controller, controller_config = _mock_controller(model)
    kwargs = {
        "controller_config": controller_config,
        "config_file": [ApplicationConfig(application="ubuntu", config=ubuntu_set_config)],
    }
    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)

    assert result == {"lma": {"ubuntu": ubuntu_expected_config}}


@pytest.mark.asyncio
async def test_apply_file_config():
    ubuntu_set_config = {"hostname": "xxx", "xx": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "xx": "44"}
    model = _mock_model(MockApp())
    retval = await apply_file_config(
        model, [ApplicationConfig(application="ubuntu", config=ubuntu_set_config)]
    )

    assert retval == {"ubuntu": ubuntu_expected_config}


@pytest.mark.asyncio
async def test_apply_configuration_get_single_config():
    model = _mock_model(MockApp())
    kwargs = {
        "config-app": "ubuntu",
        "config-get": "hostname",
    }

    result = await apply_configuration(kwargs, model)
    assert result == {"ubuntu": {"hostname": "osman"}}


@pytest.mark.asyncio
async def test_apply_configuration_get_config():
    expected = {"ubuntu": {"hostname": "osman", "xx": "xx", "others": "xx"}}
    model = _mock_model(MockApp())
    kwargs = {"config-app": "ubuntu"}

    result = await apply_configuration(kwargs, model)

    assert result == expected


@pytest.mark.asyncio
async def test_apply_configuration_set_multiple_config():
    ubuntu_set_config = {"hostname": "xxx", "xx": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "xx": "44"}

    model = _mock_model(MockApp())
    kwargs = {
        "config-app": "ubuntu",
        "config_set": ubuntu_set_config,
    }

    result = await apply_configuration(kwargs, model)
    assert result == {"ubuntu": ubuntu_expected_config}


@pytest.mark.asyncio
async def test_apply_configuration_set_from_file():
    ubuntu_set_config = {"hostname": "xxx", "xx": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "xx": "44"}

    model = _mock_model(MockApp())
    kwargs = {
        "config_file": [ApplicationConfig(application="ubuntu", config=ubuntu_set_config)],
    }
    result = await apply_configuration(kwargs, model)

    assert result == {"ubuntu": ubuntu_expected_config}


def test_values_only():
    result = values_only(FULL_CONFIG)
    assert result == SIMPLE_CONFIG


def test_values_only_with_props():
    result = values_only(FULL_CONFIG, "xx", "others")
    assert result == {"xx": "xx", "others": "xx"}
