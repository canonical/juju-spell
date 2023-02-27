"""Filter logic."""
import re
import typing as t
from dataclasses import asdict

from .config import Config, Controller

# --filter "a=v1,v2,v3 b=v4,v5,v6"
FILTER_EXPRESSION_REGEX = r"([A-Za-z]+)=([^=]+)(?:\s|$)"


def make_controllers_filter(filter_expression):
    """Build filter func to config's controller.

    If the filter_str is "a=v1,v2,v3 b=v4,v5,v6"
    This will iterate over keys [a,b] to check the value
    inside controller match the values list a in [v1,v2,v3]
    and b in [v4,v5,v6].
    """

    def serialize(values):
        if isinstance(values, str):
            return set(values.split(","))
        if isinstance(values, list):
            return set(values)
        return values

    def filter(controller: Controller):
        """Filter controllers."""
        controller_asdict = asdict(controller)
        for key, values in re.findall(
            FILTER_EXPRESSION_REGEX,
            filter_expression,
        ):
            target_val: t.Union[t.List[str], str] = controller_asdict.get(key)
            if not target_val:
                return False
            if (
                isinstance(target_val, list)
                and len(serialize(target_val) & serialize(values)) <= 0
            ):
                return False
            if isinstance(target_val, str) and asdict(controller).get(key) not in serialize(
                values
            ):
                return False
        return True

    return filter


def get_filtered_config(config: Config, filter_expression: str) -> Config:
    if filter_expression == "":
        return config

    controller_filter = make_controllers_filter(filter_expression)
    config.controllers = list(filter(controller_filter, config.controllers))
    if len(config.controllers) <= 0:
        raise ValueError("No match controller")

    return config
