import os
from datetime import datetime
from unittest import mock

import pytest
import yaml

from juju_spell.cli.list_models import (
    DATETIME_FORMATTER,
    WARNING_HEADING_TEMPLATE,
    ListModelsCMD,
)


def test_fill_parser():
    """Test add additional CLI arguments with BaseJujuCMD.."""
    parser = mock.MagicMock()
    ListModelsCMD(None).fill_parser(parser)

    parser.add_argument.assert_has_calls(
        [
            mock.call(
                "--refresh",
                default=False,
                action="store_true",
                help="This will force refresh all models from the controllers.",
            ),
        ]
    )


@pytest.mark.parametrize(
    ["retval", "expected_heading", "expected_models"],
    [
        (
            [
                {
                    "context": {
                        "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                        "name": "xxx-serverstack",
                        "customer": "Canonical",
                    },
                    "success": True,
                    "output": {
                        "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                        "name": "xxx-serverstack",
                        "data": {
                            "refresh": True,
                            "models": ["controller", "model-a", "model-b", "model-c"],
                        },
                        "timestamp": 1678256395.5965466,
                    },
                    "error": None,
                }
            ],
            "",
            {"xxx-serverstack": ["controller", "model-a", "model-b", "model-c"]},
        ),
        (
            [
                {
                    "context": {
                        "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                        "name": "yyy-serverstack",
                        "customer": "Canonical",
                    },
                    "success": True,
                    "output": {
                        "uuid": "03ascsb2-bba8-477b-854e-5715a7sb320a",
                        "name": "yyy-serverstack",
                        "data": {
                            "refresh": False,
                            "models": ["controller", "model-a", "model-b"],
                        },
                        "timestamp": 1678256395.5965466,
                    },
                    "error": None,
                }
            ],
            WARNING_HEADING_TEMPLATE.format(
                datetime.fromtimestamp(1678256395.5965466).strftime(DATETIME_FORMATTER)
            ),
            {"yyy-serverstack": ["controller", "model-a", "model-b"]},
        ),
    ],
)
def test_format_output(retval, expected_heading, expected_models):
    output = ListModelsCMD.format_output(retval)

    expected_models_str = yaml.dump(
        expected_models,
        default_flow_style=False,
        allow_unicode=True,
        encoding=None,
        sort_keys=False,
    )
    expected_output = (
        f"{expected_heading}{os.linesep}{os.linesep}{expected_models_str}{os.linesep}".lstrip()
    )
    assert expected_output == output
