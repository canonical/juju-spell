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
from __future__ import annotations

import dataclasses
import logging
import secrets
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from pathlib import Path
from time import time
from typing import Any, Dict, Iterable, List, Optional, Union

import yaml

from juju_spell.exceptions import JujuSpellError
from juju_spell.settings import DEFAULT_CACHE_DIR

logger = logging.getLogger(__name__)

DEFAULT_TTL_RULE = 3600  # in seconds
DEFAULT_AUTO_REFRESH_RULE = True


class BaseCachePolicy(dict):
    """Base class for cache policy."""

    def __init__(self, **kwargs: Any):
        """Initialize cache policy."""
        super().__init__(**kwargs)

    @classmethod
    def init_from_config(cls, cache_config: Any) -> None:
        """Load the policy from a user defined policy config."""


class DefaultCachePolicy(BaseCachePolicy):
    """A default cache policy used by any cache data."""

    def __init__(self, ttl: float, auto_refresh: bool = True):
        """Initialize default cache policy."""
        super().__init__(ttl=ttl, auto_refresh=auto_refresh)


class Cache(metaclass=ABCMeta):
    """A cache for command's output with cache policy."""

    policy: DefaultCachePolicy = DefaultCachePolicy(
        ttl=DEFAULT_TTL_RULE, auto_refresh=DEFAULT_AUTO_REFRESH_RULE
    )

    @property
    @abstractmethod
    def expired(self) -> bool:
        """Check if the cache is expired or not."""

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get data from the cache, need to implement by the subclass."""

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Update the cache's data, need to implement by the subclass."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the changes to the cache, need to implement by the subclass."""

    @classmethod
    @abstractmethod
    def connect(cls, backend: Any) -> Any:
        """Connect to the cache backend, need to implement by the subclass."""


@dataclasses.dataclass()
class FileCacheContext:
    """A context for holding file cache data."""

    uuid: str = ""
    name: str = ""
    data: Dict[str, Any] = dataclasses.field(default_factory=dict)
    timestamp: float = time()


class FileCache(Cache, FileCacheContext):
    """Create a cache file to store the data."""

    cache_name: Union[str, Path] = ""
    cache_directory: Path = DEFAULT_CACHE_DIR

    @property
    def expired(self) -> bool:
        """Check if the cache is expired or not."""
        return self.timestamp + self.policy["ttl"] < time()

    @property
    def context(self) -> Dict[str, Any]:
        """Get the file cache context as a dictionary."""
        return dataclasses.asdict(self)

    def put(self, key: str, value: Any) -> None:
        """Change file cache data."""
        setattr(self, key, value)

    def get(self, key: str) -> Any:
        """Get data from the file cache."""
        return getattr(self, key)

    def update(self, **kwargs: Any) -> None:
        """Update file cache data in a batch."""
        for key, value in kwargs.items():
            self.put(key, value)

    def commit(self, name: Optional[Union[str, Path]] = "") -> None:
        """Commit file cache to the default cache directory named by `name`."""
        if not self.cache_directory.exists():
            self.cache_directory.mkdir()
        if self.cache_name == "" and name == "":
            raise JujuSpellError(
                "failed to write commit file cache: missing 'name' for file cache."
            )
        if name:
            self.cache_name = name
        fname = self.cache_directory / self.cache_name
        try:
            with open(fname, "w", encoding="UTF-8") as file:
                data = yaml.safe_dump(self.context)
                logger.debug("save cache file to %s", str(fname))
                file.write(data)
        except PermissionError as error:
            raise JujuSpellError(f"permission denied to write to file `{fname}`.") from error
        except Exception as error:
            raise JujuSpellError(f"{str(error)}.") from error

    @classmethod
    def connect(cls, backend: Union[str, Path]) -> FileCache:
        """Connect to file cache in the default cache directory named by `backend`."""
        cls.cache_name = cls.cache_directory / backend
        try:
            with open(cls.cache_name, "r", encoding="UTF-8") as file:
                data = yaml.safe_load(file)
                logger.debug("load cache file from %s", str(cls.cache_name))
                return cls(**data)
        except FileNotFoundError as error:
            raise JujuSpellError(f"`{cls.cache_name}` does not exists.") from error
        except PermissionError as error:
            raise JujuSpellError(
                f"permission denied to read from file `{cls.cache_name}`."
            ) from error
        except Exception as error:
            raise JujuSpellError(f"{str(error)}.") from error


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


def load_yaml_file(path: Path) -> Any:
    """Load yaml file.

    raises: IsADirectoryError if path is directory
    raises: FileNotFoundError -> JujuSpellError if fies does not exist
    raises: PermissionError -> JujuSpellError if user has no permission to path
    """
    try:
        with open(path, "r", encoding="UTF-8") as file:
            source = yaml.safe_load(file)
            logger.info("load yaml file from %s path", path)
            return source
    except FileNotFoundError as error:
        raise JujuSpellError(f"patch file {path} does not exist") from error
    except PermissionError as error:
        raise JujuSpellError(f"permission denied to read patch file {path}") from error
