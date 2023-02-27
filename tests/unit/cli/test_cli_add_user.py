import pytest
import yaml

from juju_spell.cli.add_user import AddUserCMD
from juju_spell.settings import PERSONAL_CONFIG_PATH


@pytest.mark.parametrize(
    ["retval", "excepted_leading_word", "excepted_data"],
    [
        (
            [
                {
                    "context": {
                        "uuid": "ea3229b3-1ecf-4fa5-bf5a-e8885ab2de57",
                        "name": "controller1",
                    },
                    "output": {
                        "user": "new-user",
                        "display_name": "new-user-display-name",
                        "password": "new-user-pwd",
                    },
                    "error": None,
                }
            ],
            f"Please put user information to personal config({PERSONAL_CONFIG_PATH}):",
            {
                "controllers": [
                    {
                        "uuid": "ea3229b3-1ecf-4fa5-bf5a-e8885ab2de57",
                        "name": "controller1",
                        "user": "new-user",
                        "password": "new-user-pwd",
                    }
                ]
            },
        ),
    ],
)
def test_add_user_cmd_format_output(retval, excepted_leading_word, excepted_data):
    output = AddUserCMD.format_output(retval)
    assert excepted_leading_word in output

    assert yaml.safe_load(output.replace(excepted_leading_word, "").strip()) == excepted_data
