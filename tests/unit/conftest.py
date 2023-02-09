import io
from pathlib import Path

import pytest
import yaml

from juju_spell.config import Config, Connection, Controller

TEST_CONFIG = """
controllers:
  - name: example_controller
    uuid: c29e8cf7-9380-4d2f-91bb-ac4d9f26a60c
    customer: example_customer
    owner: Gandalf
    description: some nice notes
    tags: ["test"]
    risk: 3
    endpoint: 10.1.1.46:17070
    ca_cert: |
        -----BEGIN CERTIFICATE-----
        1234
        -----END CERTIFICATE-----
    model_mapping:
      lma: monitoring
      default: production
    connection:
      destination: ubuntu@10.1.1.99
      subnets:  # optional (sshuttle)
        - 10.1.1.0/24
        - 20.1.1.0/24
      jumps:
        - bastion
  - name: example_controller_without_optional
    uuid: 1f918f78-97ab-47d2-b3a5-4b15fd75b67b
    customer: example_customer
    owner: Gandalf
    endpoint: 10.1.1.47:17070
    ca_cert: |
        -----BEGIN CERTIFICATE-----
        1234
        -----END CERTIFICATE-----
    model_mapping:
      lma: monitoring
      default: production
"""

TEST_PERSONAL_CONFIG = """
controllers:
  - name: example_controller
    uuid: c29e8cf7-9380-4d2f-91bb-ac4d9f26a60c
    user: admin
    password: pass1234
  - name: example_controller_without_optional
    uuid: 1f918f78-97ab-47d2-b3a5-4b15fd75b67b
    user: admin
    password: pass1234
"""

# A Merged config(TEST_CONFIG and TEST_PERSONAL_CONFIG)
TEST_COMPLETE_CONFIG = """
controllers:
  - name: example_controller
    uuid: c29e8cf7-9380-4d2f-91bb-ac4d9f26a60c
    customer: example_customer
    owner: Gandalf
    description: some nice notes
    tags: ["test"]
    risk: 3
    endpoint: 10.1.1.46:17070
    ca_cert: |
        -----BEGIN CERTIFICATE-----
        1234
        -----END CERTIFICATE-----
    model_mapping:
      lma: monitoring
      default: production
    connection:
      destination: ubuntu@10.1.1.99
      subnets:  # optional (sshuttle)
        - 10.1.1.0/24
        - 20.1.1.0/24
      jumps:
        - bastion
    user: admin
    password: pass1234
  - name: example_controller_without_optional
    uuid: 1f918f78-97ab-47d2-b3a5-4b15fd75b67b
    customer: example_customer
    owner: Gandalf
    endpoint: 10.1.1.47:17070
    ca_cert: |
        -----BEGIN CERTIFICATE-----
        1234
        -----END CERTIFICATE-----
    model_mapping:
      lma: monitoring
      default: production
    user: admin
    password: pass1234
"""


@pytest.fixture
def test_config_path(tmp_path) -> Path:
    """Return path to test global config."""
    path = tmp_path / "global_config.yaml"
    with open(path, "w") as file:
        file.write(TEST_CONFIG)

    return path


@pytest.fixture
def test_personal_config_path(tmp_path) -> Path:
    """Return path to test personal config."""
    path = tmp_path / "personal_config.yaml"
    with open(path, "w") as file:
        file.write(TEST_PERSONAL_CONFIG)

    return path


@pytest.fixture
def test_config_dict():
    """Return config file as dict."""
    return yaml.safe_load(TEST_COMPLETE_CONFIG)


@pytest.fixture
def test_config(test_config_dict):
    """Return config file as dict."""
    return Config(**test_config_dict)


@pytest.fixture
def controller_config(test_config_dict):
    """Return first controller configuration form test config."""
    controller = test_config_dict["controllers"][0]
    controller["connection"] = Connection(controller["connection"])
    return Controller(**controller)


@pytest.fixture(name="mock_load_config_file_func")
def fixture_mock_load_config_file(test_config_path, test_personal_config_path):
    def _mock_func(path):
        if path == test_config_path:
            return yaml.safe_load(io.StringIO(TEST_CONFIG))
        if path == test_personal_config_path:
            return yaml.safe_load(io.StringIO(TEST_PERSONAL_CONFIG))
        return ""

    return _mock_func
