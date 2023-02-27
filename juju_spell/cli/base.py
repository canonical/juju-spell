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

"""JujuSpell base cli command."""
import argparse
import asyncio
import json
import os
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from craft_cli import BaseCommand, emit
from craft_cli.dispatcher import _CustomArgumentParser

from juju_spell.assignment.runner import run
from juju_spell.cli.utils import confirm, parse_comma_separated_str, parse_filter
from juju_spell.commands.base import BaseJujuCommand
from juju_spell.config import Config
from juju_spell.exceptions import JujuSpellError
from juju_spell.filter import get_filtered_config


class BaseCMD(BaseCommand, metaclass=ABCMeta):
    """Base CLI command for handling contexts."""

    def __init__(self, config: Optional[Config]) -> None:
        """Initialize BaseCMD."""
        self.config: Optional[Config] = None  # to overwrite config type hinting
        super().__init__(config)

    def run(self, parsed_args: argparse.Namespace) -> Optional[int]:
        """Execute CLI command.

        **This function should not be changed.**
        """
        try:
            self.before(parsed_args)
            emit.trace(f"function 'before' was run for {self.name} command")
            retval = self.execute(parsed_args)
            emit.trace(f"raw output of {self.name} command: {retval}")
            message = self.format_output(retval)
            emit.message(message)  # print the output
            self.after(parsed_args)
            emit.trace(f"function 'after' was run for {self.name} command")
            return 0
        except Exception as error:
            raise JujuSpellError(
                f"{self.name} failed to run with error{os.linesep}  {error}"
            ) from error

    @staticmethod
    def format_output(retval: Any) -> str:
        """Pretty formatter for output."""
        emit.debug(f"formatting `{retval}`")
        if isinstance(retval, (dict, list)):
            # TODO: add support for table, yaml, ... format
            return json.dumps(retval, default=vars, indent=1)

        return str(retval)

    @abstractmethod
    def execute(self, parsed_args: argparse.Namespace) -> Any:  # pragma: no cover
        """Abstract function need to be defined for each JujuSpell CLI command."""
        ...

    def before(self, parsed_args: argparse.Namespace) -> None:  # pragma: no cover
        """Run before execution."""
        ...

    def after(self, parsed_args: argparse.Namespace) -> None:  # pragma: no cover
        """Run after execution."""
        ...

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            default=False,
            action="store_true",
            help=("This will only run pre-check and dry-run only instead of real execution."),
        )


class BaseJujuCMD(BaseCMD, metaclass=ABCMeta):
    """Base CLI command for handling any Juju commands."""

    @property
    @abstractmethod
    def command(self):  # pragma: no cover
        ...

    def fill_parser(self, parser: _CustomArgumentParser) -> None:
        """Define base arguments for Juju commands.

        This will add arguments for connection, filtering and config.
        """
        super().fill_parser(parser)
        parser.add_argument(
            "--no-confirm",
            default=False,
            action="store_true",
            help="This will skip all the confirm check.",
        )
        parser.add_argument(
            "--run-type",
            type=str,
            choices=["parallel", "batch", "serial"],
            default="serial",
            help="parallel, batch or serial",
        )
        parser.add_argument(
            "--filter",
            type=parse_filter,
            required=False,
            default="",
            help=(
                "Key-value pair comma separated string in double quotes e.g., "
                '"a=1,2,3 b=4,5,6". '
            ),
        )
        parser.add_argument(
            "--models",
            type=parse_comma_separated_str,
            help="model filter",
        )

    def execute(self, parsed_args: argparse.Namespace) -> Any:
        """Execute Juju Commands."""
        if self.command is None or not issubclass(self.command, BaseJujuCommand):
            raise RuntimeError(f"command `{self.command}` is incorrect")

        filtered_config = get_filtered_config(self.config, parsed_args.filter)
        loop = asyncio.get_event_loop()
        task = loop.create_task(run(filtered_config, self.command(), parsed_args))
        loop.run_until_complete(asyncio.gather(task))
        return task.result()


class JujuReadCMD(BaseJujuCMD, metaclass=ABCMeta):
    """Base CLI command for handling Juju commands with read access."""


class JujuWriteCMD(BaseJujuCMD, metaclass=ABCMeta):
    """Base CLI command for handling Juju commands with write access."""

    abort = False

    def run(self, parsed_args: argparse.Namespace) -> Optional[int]:
        """Execute CLI command for JujuCommands."""
        if not parsed_args.no_confirm and not confirm(
            text=f"Continue on cmd: {self.name} parsed_args: {parsed_args}",
            abort=self.abort,
        ):
            return 0

        return super().run(parsed_args)
