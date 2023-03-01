import os
from unittest import mock

import pytest
import yaml

from juju_spell.cli.list_models import WARNING_HEADING, ListModelsCMD


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
                help=(
                    "This will force refresh all models from the controllers. (TODO: to"
                    " be implemented)"
                ),
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
                        "refresh": True,
                        "models": ["controller", "model-a", "model-b", "model-c"],
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
                        "refresh": False,
                        "models": ["controller", "model-a", "model-b"],
                    },
                    "error": None,
                }
            ],
            WARNING_HEADING,
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
        f"{expected_heading}{os.linesep}{os.linesep}{expected_models_str}{os.linesep}"
        .lstrip()
    )
    assert expected_output == output
