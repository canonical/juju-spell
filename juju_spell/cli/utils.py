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

"""Unilities."""
import re
import sys
from argparse import ArgumentTypeError
from gettext import gettext
from typing import Callable, List

from craft_cli import emit

from juju_spell.exceptions import Abort, JujuSpellError
from juju_spell.filter import FILTER_EXPRESSION_REGEX

visible_prompt_func: Callable[[str], str] = input


def _get_value_from_prompt(prompt: str) -> str:
    """Get value from prompt."""
    try:
        with emit.pause():
            return visible_prompt_func(prompt).strip()
    except (KeyboardInterrupt, EOFError):
        raise Abort("Aborted by user") from None


def confirm(
    text: str,
    default: bool = True,
    abort: bool = False,
    prompt_suffix: str = ": ",
) -> bool:
    """Prompts for confirmation (yes/no question).

    If the user aborts the input by sending an interrupt signal this
    function will catch it and raise a :exc:`Abort` exception.

    If stdin is not a tty, the :exc:`JujuSpellError` exception will be raised.

    If user returns an empty answer, the default value is returned.
    returns default value.

    :param text: the question to ask.
    :param default: default answer
    :param abort: if this is set to `True` a negative answer aborts the
                  exception by raising :exc:`Abort`.
    :param prompt_suffix: a suffix that should be added to the prompt.
    """
    if not sys.stdin.isatty():
        raise JujuSpellError(
            "Could not confirm without terminal session. Please use `--no-confirm` or"
            "run in virtual terminal session."
        )

    choices: str = "Y/n" if default else "N/y"
    prompt = f"{text}[{choices}]{prompt_suffix}"

    while True:
        value = _get_value_from_prompt(prompt).lower()

        if not value:  # pylint: disable=R1705
            return default
        elif value in ("y", "yes"):
            return True
        elif value in ("n", "no") and abort:
            raise Abort("Aborted by user")
        elif value in ("n", "no"):
            return False

        emit.message(gettext("Error: invalid input"))


def parse_comma_separated_str(comma_separated_str: str) -> List[str]:
    """Parse comma separated string."""
    result = comma_separated_str.split(",")
    return [obj.strip() for obj in result if obj]


def parse_filter(value: str) -> str:
    """Type check for argument filter."""
    if not (re.findall(FILTER_EXPRESSION_REGEX, value) or len(value) == 0):
        raise ArgumentTypeError(f"Argument filter format wrong: {value}")

    return value
