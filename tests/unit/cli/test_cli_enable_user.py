from unittest import mock

from juju_spell.cli.enable_user import EnableUserCMD


def test_enable_user_cmd_fill_parser():
    """Test add additional CLI arguments with BaseCMD."""
    parser = mock.MagicMock()
    EnableUserCMD(config=None).fill_parser(parser)

    parser.add_argument.assert_has_calls(
        [
            mock.call("--user", type=str, help="username to enable", required=True),
        ]
    )
