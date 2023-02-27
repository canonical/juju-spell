from argparse import ArgumentTypeError
from unittest import mock

import pytest

from juju_spell.cli.utils import (
    _get_value_from_prompt,
    confirm,
    parse_comma_separated_str,
    parse_filter,
)
from juju_spell.exceptions import Abort, JujuSpellError


@mock.patch("juju_spell.cli.utils.emit")
@mock.patch("juju_spell.cli.utils.visible_prompt_func")
def test_get_value_from_prompt(mock_visible_prompt_func, mock_emit):
    """Test get value from prompt."""
    prompt = "test: [Y/n]"

    _get_value_from_prompt(prompt)

    mock_emit.pause.assert_called_once()
    mock_visible_prompt_func.assert_called_once_with(prompt)


@mock.patch("juju_spell.cli.utils.emit")
@mock.patch("juju_spell.cli.utils.visible_prompt_func")
def test_get_value_from_prompt_exception(mock_visible_prompt_func, _):
    """Test get value from prompt."""
    prompt = "test: [Y/n]"
    mock_visible_prompt_func.side_effect = KeyboardInterrupt

    with pytest.raises(Abort):
        _get_value_from_prompt(prompt)


@pytest.mark.parametrize(
    "inputs, kwargs, exp_result",
    [
        ([""], {}, True),
        ([""], {"default": True}, True),
        ([""], {"default": False}, False),
        (["u", "uu", "uuu", "y1", "y"], {}, True),
        (["Y"], {}, True),
        (["b", "bb", "bbb", "b1", "n"], {}, False),
        (["N"], {}, False),
    ],
)
@mock.patch("juju_spell.cli.utils._get_value_from_prompt")
@mock.patch("juju_spell.cli.utils.sys.stdin.isatty", return_value=True)
def test_confirm(_, mock_get_value_from_prompt, inputs, kwargs, exp_result):
    """Test config function."""
    prompt = "test: [Y/n]"
    mock_get_value_from_prompt.side_effect = inputs

    result = confirm(prompt, abort=False, **kwargs)

    assert result == exp_result


@pytest.mark.parametrize("inputs", [["b", "bb", "bbb", "b1", "n"], ["N"]])
@mock.patch("juju_spell.cli.utils._get_value_from_prompt")
@mock.patch("juju_spell.cli.utils.sys.stdin.isatty", return_value=True)
def test_confirm_abort(_, mock_get_value_from_prompt, inputs):
    """Test config function."""
    prompt = "test: [Y/n]"
    mock_get_value_from_prompt.side_effect = inputs

    with pytest.raises(Abort):
        confirm(prompt, abort=True)


@mock.patch("juju_spell.cli.utils.sys.stdin.isatty", return_value=False)
def test_confirm_not_in_tty(mock_isatty):
    """Test raising exception if stdin is not a tty."""
    prompt = "test: [Y/n]"

    with pytest.raises(JujuSpellError):
        confirm(prompt)

    mock_isatty.assert_called_once()


@pytest.mark.parametrize(
    "string, exp_list",
    [("a,b,c,", ["a", "b", "c"]), (",a,b,c,", ["a", "b", "c"]), (",", [])],
)
def test_parse_comma_separated_str(string, exp_list):
    """Test parsing list from string separated by comma."""
    result = parse_comma_separated_str(string)

    assert result == exp_list


@pytest.mark.parametrize("value", ["a=1", "a=1,b=2,c='Gandalf'", "a=v1,v2,v3 b=v4,v5,v6"])
def test_parse_filter(value):
    """Test parse_filter with valid format."""
    result = parse_filter(value)

    assert result == value


@pytest.mark.parametrize("value", ["1=2", "1", "22='Gandalf'"])
def test_parse_filter_exception(value):
    """Test parse_filter raising exception."""
    with pytest.raises(ArgumentTypeError):
        parse_filter(value)
