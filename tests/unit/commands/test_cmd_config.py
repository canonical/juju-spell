from typing import Dict
from unittest.mock import AsyncMock

import pytest as pytest

from juju_spell.commands.config import (
    ApplicationConfig,
    ConfigCommand,
    apply_configuration,
    apply_file_config,
)


class MockApp:
    properties: Dict = {}

    def __init__(self, props: Dict[str, str]):
        """Initialize with dictionary."""
        self.properties = props

    async def set_config(self, props: Dict[str, str]):
        self.properties.update(props)

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
    ubuntu_config = {"hostname": "test-test", "cpu": "2"}
    model = _mock_model(MockApp(ubuntu_config))
    controller, controller_config = _mock_controller(model)
    kwargs = {
        "config_app": "ubuntu",
        "config_get": "hostname",
        "controller_config": controller_config,
    }

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)
    assert result == {"lma": {"ubuntu": {"hostname": "test-test"}}}


@pytest.mark.asyncio
async def test_execute_get_config():
    ubuntu_config = {"hostname": "test-test", "cpu": "2"}
    model = _mock_model(MockApp(ubuntu_config))
    controller, controller_config = _mock_controller(model)
    kwargs = {"config_app": "ubuntu", "controller_config": controller_config}

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)

    assert result == {"lma": {"ubuntu": ubuntu_config}}


@pytest.mark.asyncio
async def test_execute_set_multiple_config():
    ubuntu_config = {"hostname": "test-test", "cpu": "2", "others": "ok"}
    ubuntu_set_config = {"hostname": "xxx", "cpu": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "cpu": "44", "others": "ok"}

    model = _mock_model(MockApp(ubuntu_config))
    controller, controller_config = _mock_controller(model)
    kwargs = {
        "config_app": "ubuntu",
        "controller_config": controller_config,
        "config_set": ubuntu_set_config,
    }

    config_cmd: ConfigCommand = ConfigCommand()
    result = await config_cmd.execute(controller=controller, models=["lma"], **kwargs)

    assert result == {"lma": {"ubuntu": ubuntu_expected_config}}


@pytest.mark.asyncio
async def test_execute_set_from_file():
    ubuntu_config = {"hostname": "test-test", "cpu": "2", "others": "ok"}
    ubuntu_set_config = {"hostname": "xxx", "cpu": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "cpu": "44", "others": "ok"}

    model = _mock_model(MockApp(ubuntu_config))
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
    ubuntu_config = {"hostname": "test-test", "cpu": "2", "others": "ok"}
    ubuntu_set_config = {"hostname": "xxx", "cpu": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "cpu": "44", "others": "ok"}
    model = _mock_model(MockApp(ubuntu_config))
    retval = await apply_file_config(
        model, [ApplicationConfig(application="ubuntu", config=ubuntu_set_config)]
    )

    assert retval == {"ubuntu": ubuntu_expected_config}


@pytest.mark.asyncio
async def test_apply_configuration_get_single_config():
    ubuntu_config = {"hostname": "test-test", "cpu": "2"}
    model = _mock_model(MockApp(ubuntu_config))
    kwargs = {
        "config_app": "ubuntu",
        "config_get": "hostname",
    }

    result = await apply_configuration(kwargs, model)
    assert result == {"ubuntu": {"hostname": "test-test"}}


@pytest.mark.asyncio
async def test_apply_configuration_get_config():
    ubuntu_config = {"hostname": "test-test", "cpu": "2"}
    model = _mock_model(MockApp(ubuntu_config))
    kwargs = {"config_app": "ubuntu"}

    result = await apply_configuration(kwargs, model)

    assert result == {"ubuntu": ubuntu_config}


@pytest.mark.asyncio
async def test_apply_configuration_set_multiple_config():
    ubuntu_config = {"hostname": "test-test", "cpu": "2", "others": "ok"}
    ubuntu_set_config = {"hostname": "xxx", "cpu": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "cpu": "44", "others": "ok"}

    model = _mock_model(MockApp(ubuntu_config))
    kwargs = {
        "config_app": "ubuntu",
        "config_set": ubuntu_set_config,
    }

    result = await apply_configuration(kwargs, model)
    assert result == {"ubuntu": ubuntu_expected_config}


@pytest.mark.asyncio
async def test_apply_configuration_set_from_file():
    ubuntu_config = {"hostname": "test-test", "cpu": "2", "others": "ok"}
    ubuntu_set_config = {"hostname": "xxx", "cpu": "44"}
    ubuntu_expected_config = {"hostname": "xxx", "cpu": "44", "others": "ok"}

    model = _mock_model(MockApp(ubuntu_config))
    kwargs = {
        "config_file": [ApplicationConfig(application="ubuntu", config=ubuntu_set_config)],
    }
    result = await apply_configuration(kwargs, model)

    assert result == {"ubuntu": ubuntu_expected_config}
