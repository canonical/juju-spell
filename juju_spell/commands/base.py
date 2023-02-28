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

"""JujuSpell base juju command."""
import dataclasses
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from juju.controller import Controller
from juju.model import Model

from juju_spell.exceptions import JujuSpellError


@dataclasses.dataclass(frozen=True)
class Result:
    """Result from command."""

    success: bool
    output: Optional[Any] = None
    error: Optional[Exception] = None


class BaseJujuCommand(metaclass=ABCMeta):
    """Base Juju commands."""

    def __init__(self) -> None:
        """Init for command."""
        self.name = getattr(self.__class__, "__name__", "unknown")
        self.logger = logging.getLogger(self.name)

    @staticmethod
    async def get_filtered_models(
        controller: Controller,
        model_mappings: Dict[str, List[str]],
        models: Optional[List[str]] = None,
    ) -> AsyncGenerator[Tuple[str, Model], None]:
        """Get filtered models for controller.

        If models is None, then all models for controller will be returned.
        If the model_mapping[model] exits for specific model it will be replaced by the
        list of values from model_mapping[model] from config.
        """
        if models is None or len(models) <= 0:
            all_models = await controller.list_models()
        else:
            all_models = _apply_model_mappings(models, model_mappings)

        for model_name in all_models:
            model = await controller.get_model(model_name)
            yield model_name, model
            await model.disconnect()

    # pylint: disable=W0613
    async def pre_check(self, controller: Controller, **kwargs: Any) -> Optional[Result]:
        """Run pre-check for command."""
        self.logger.debug("%s running pre-check", controller.controller_uuid)
        if not controller.is_connected():
            self.logger.info(
                "%s pre-check: controller is connected",
                controller.controller_uuid,
            )
            return Result(
                False,
                error=JujuSpellError(f"controller {controller.controller_uuid} is not connected"),
            )

        return None

    # pylint: disable=W0613
    async def dry_run(self, controller: Controller, **kwargs: Any) -> Result:
        """Dry-run will output the necessary information of the target."""
        self.logger.info("%s running dry-run", controller.controller_uuid)
        return Result(
            success=True,
            output={
                "target": controller.controller_uuid,
                "command_doc": self.execute.__doc__,
            },
        )

    async def run(self, controller: Controller, **kwargs: Any) -> Result:
        """Execute Juju command.

        **This function should not be changed.**
        """
        self.logger.info("%s running %s command", controller.controller_uuid, self.name)
        try:
            output = await self.execute(controller, **kwargs)
            if not isinstance(output, Result):
                output = Result(True, output=output)

            return output
        except Exception as error:  # pylint: disable=W0718
            self.logger.exception(error)
            return Result(False, output=None, error=error)

    @property
    def need_sshuttle(self) -> bool:
        """Check if sshuttle is needed."""
        return False

    @abstractmethod
    async def execute(
        self,
        controller: Controller,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # pragma: no cover
        """Execute function.

        This part will be the main part function
        Args:
            controller: This will be juju controller
            kwargs: This will be the kwargs passed to the function which
                will contain the config for the selected controller
        """


def _apply_model_mappings(
    models: List[str],
    model_mappings: Optional[Dict[str, List[str]]],
) -> List[str]:
    """Replace the models with values from model_mappings.

    If --model parameter is provided searches the map for matching model, if found
    puts the corresponding values from controller.model_mapping into results if not
    found puts the model itself to results.
    Args:
        models: list of models from input
        model_mappings: mappings from config file
    Returns:
        list of models replaced with values from model_mappings
    """
    if model_mappings is None or len(model_mappings) <= 0:
        return models

    results = []
    for model in models:
        model_list = model_mappings.get(model, [model])
        model_list = model_list if len(model_list) > 0 else [model]
        results.extend(model_list)

    return results
