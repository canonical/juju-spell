# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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

"""JujuSpell juju config command."""
import argparse
import logging
import textwrap
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell import utils
from juju_spell.cli.base import JujuWriteCMD
from juju_spell.commands.config import ApplicationConfig, ConfigCommand

logger = logging.getLogger()


class ConfigCMD(JujuWriteCMD):
    """JujuSpell juju config command."""

    name = "config"
    help_msg = "Gets, sets, or resets configuration for a deployed application"
    overview = textwrap.dedent(
        """
        The config command gets or sets the config options on applications.

        Example:
        $ juju-spell config --config-app nova-compute
        [
         {
          "context": {
            ...
          },
          "success": true,
          "output": {
            "my_model": {
              "my_application": {
                "config_item": {
                  "default": "",
                  "description": "",
                  "source": "",
                  "type": "",
                  "value": ""
                },
              }
            }
           }
          },
          "error": null
         }
        ]

        $ juju-spell config --config-app nova-compute --config-get config_item
        $ juju-spell config --config-app nova-compute --config-set "a=1" "b=3"

        With --file option multiple application configurations can be changed.
        $ juju-spell config --config-file config.yaml

        $ cat config.yaml
        squid-reverseproxy:
          cache_size_mb: "129"
          cache_mem_mb: "257"
        ubuntu:
          hostname: "my-ubuntu-host"


        """
    )
    command = ConfigCommand

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        """Add arguments specific to the export-login command."""
        super().fill_parser(parser)
        parser.add_argument(
            "config-app",
            nargs="?",
            help="The application to show/update configuration.",
        )
        parser.add_argument(
            "config-get",
            type=str,
            nargs="?",
            help="Single property to get.",
        )
        parser.add_argument(
            "--config-set",
            nargs="*",
            required=False,
            action=KeyValue,
            help="key=value pairs to update application config.",
        )
        parser.add_argument(
            "--config-file",
            type=get_application_config,
            required=False,
            help="The path to yaml-formatted application config.",
        )


def get_application_config(path: str) -> List[ApplicationConfig]:
    """Parse application config to model."""
    yaml_config = utils.load_yaml_file(Path(path))
    result: List[ApplicationConfig] = []
    for app, value_dict in yaml_config.items():
        application_config = ApplicationConfig(application=app, config=value_dict)
        result.append(application_config)
    return result


# pylint: disable=too-few-public-methods
class KeyValue(argparse.Action):
    """Parse parameters as key=value pairs."""

    def __call__(
        self,
        _: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: Optional[str] = None,
    ) -> None:
        setattr(namespace, self.dest, {})
        if values:
            for value in values:
                key, value = value.split("=", 1)
                getattr(namespace, self.dest)[key] = value
