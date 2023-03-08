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

"""Command entrypoint for ListModelsCommand."""
import os
import textwrap
from datetime import datetime
from typing import Any

import yaml
from craft_cli import emit
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.cli.base import JujuReadCMD
from juju_spell.commands.list_models import ListModelsCommand

WARNING_HEADING_TEMPLATE = (
    f"Use --refresh option with this command to see the latest information.{os.linesep*2}"
    "(Last updated: {})"
)
DATETIME_FORMATTER = "%Y-%m-%d %H:%M:%S"


class ListModelsCMD(JujuReadCMD):
    """List models from the local cache or from the controllers."""

    name = "list-models"
    help_msg = "Return the list of models from the local cache or from the controllers."
    overview = textwrap.dedent(
        """
        The list-models command shows the list of models from the local cache
        or from the controllers.

        Example:
        $ juju-spell list-models --refresh

        controller-a:
        - model-a
        - model-b
        - model-c
        controller-b:
        - model-a
        - model-b
        - model-c

        $ juju-spell list-models
        Use --refresh option with this command to see the latest information.

        (Last updated: 2004-03-05 00:00:00)

        controller-a:
        - model-a
        - model-b
        - model-c
        controller-b:
        - model-a
        - model-b
        - model-c
        """
    )
    command = ListModelsCommand

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        super().fill_parser(parser)
        parser.add_argument(
            "--refresh",
            default=False,
            action="store_true",
            help="This will force refresh all models from the controllers.",
        )

    @staticmethod
    def format_output(retval: Any) -> str:
        """Pretty formatter for output.

        The first element of retval, which is a list of models from all
        controllers' output. For example:

        [
            {
                "context": {
                    "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                    "name": "xxx-serverstack",
                    "customer": "Canonical"
                },
                "success": true,
                "output": {
                    "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                    "name": "xxx-serverstack",
                    "models": [
                        "controller",
                        "model-a",
                        "model-b",
                        "model-c"
                    ],
                    "refresh": true,
                    "timestamp": 1078416000.0
                },
                "error": null
            }
        ]
        """
        emit.debug(f"formatting `{retval}`")

        controller_models_mapping = {}

        heading = ""
        for outputs in retval:
            controller_name = outputs["context"]["name"]
            models = outputs["output"]["models"]
            refresh = outputs["output"]["refresh"]
            controller_models_mapping[controller_name] = models
            if not refresh:
                timestamp = float(outputs["output"]["timestamp"])
                heading = WARNING_HEADING_TEMPLATE.format(
                    datetime.fromtimestamp(timestamp).strftime(DATETIME_FORMATTER)
                )

        yaml_str = yaml.dump(
            controller_models_mapping,
            default_flow_style=False,
            allow_unicode=True,
            encoding=None,
            sort_keys=False,
        )
        return f"{heading}{os.linesep}{os.linesep}{yaml_str}{os.linesep}".lstrip()
