# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021-2022 Canonical Ltd.
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

"""Utilities for JujuSpell."""
import secrets
from collections import defaultdict
from typing import Dict, Iterable, List


def strtobool(value: str) -> bool:
    """Convert a string representation of truth to true (1) or false (0).

    :param value: a True value of 'y', 'yes', 't', 'true', 'on', and '1'
        or a False value of 'n', 'no', 'f', 'false', 'off', and '0'.
    :raises ValueError: if `value` is not a valid boolean value.
    """
    parsed_value = value.lower()

    if parsed_value in ("y", "yes", "t", "true", "on", "1"):
        return True
    if parsed_value in ("n", "no", "f", "false", "off", "0"):
        return False

    raise ValueError(f"Invalid boolean value of {value!r}")


def humanize_list(
    items: Iterable[str],
    conjunction: str,
    item_format: str = "{!r}",
    sort: bool = True,
) -> str:
    """Format a list into a human-readable string.

    :param items: list to humanize.
    :param conjunction: the conjunction used to join the final element to
                        the rest of the list (e.g. 'and').
    :param item_format: format string to use per item.
    :param sort: if true, sort the list.
    """
    if not items:
        return ""

    quoted_items = [item_format.format(item) for item in items]

    if sort:
        quoted_items = sorted(quoted_items)

    if len(quoted_items) == 1:
        return quoted_items[0]

    humanized = ", ".join(quoted_items[:-1])

    if len(quoted_items) > 2:
        humanized += ","

    return f"{humanized} {conjunction} {quoted_items[-1]}"


def merge_list_of_dict_by_key(key: str, lists: List[List[Dict]]) -> List:
    """Merge multiple list of dict by key.

    Example:
        a = [{"index": 1, "v": "a"}, {"index": 2, "v": "a"}, {"index": 3, "v": "a"}]
        b = [{"index": 1, "v": "b"}, {"index": 2, "u": "b"}, {"index": 4, "v": "b"}]

        result = merge_list_of_dict_by_key(a, b)

        result: [
            {"index": 1, "v": "b"},
            {"index": 2, "v": "b", "u": "b"},
            {"index": 3, "v": "a"},
            {"index": 4, "v": "b"},
        ]
    """
    new_dict: Dict = defaultdict(dict)
    for _list in lists:
        for elem in _list:
            new_dict[elem[key]].update(elem)
    return list(new_dict.values())


def random_password(length: int = 30) -> str:
    """Generate random password."""
    return secrets.token_urlsafe(length)
