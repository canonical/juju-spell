"""Contains constants settings of the package."""
import os
import pathlib

APP_NAME = "juju-spell"
APP_VERSION = "0.0.1"
JUJUSPELL_DATA = pathlib.Path(
    os.environ.get(
        "JUJUSPELL_DATA",
        pathlib.Path(
            # The $HOME will be /snap/juju-spell/current after snap packaging.
            # We need to use $SNAP_REAL_HOME to get the real user's
            # home directory in snap.
            os.environ.get("SNAP_REAL_HOME", pathlib.Path.home())
        )
        / ".local/share/juju-spell",
    )
)

CONFIG_PATH = os.environ.get(
    "JUJUSPELL_CONFIG",
    pathlib.Path(JUJUSPELL_DATA / "config.yaml"),
)
PERSONAL_CONFIG_PATH = os.environ.get(
    "JUJUSPELL_PERSONAL_CONFIG", pathlib.Path(JUJUSPELL_DATA / "config.personal.yaml")
)
DEFAULT_PORT_RANGE = range(17071, 17170)
DEFAULT_RETRY_BACKOFF = 1.5  # seconds
DEFAULT_CONNECTIN_TIMEOUT = 60  # seconds
DEFAULT_CONNECTIN_WAIT = 1  # seconds
DEFUALT_MAX_FRAME_SIZE = 6**24


CROSS_FINGERS = """
JujuSpell
                                            @@@@@@@
                                        @@@@@@@@@     @@
                                       @@      @@     @@
                                        @@     @@@   @@
                                        @@      @@  @@
                                         @@      @@(@@
                                         ,@@      @@@
                                          @@      @@@
                                  &@&    @@@@      @@
                              *@@%   @@@@@ #@@      @@
                            .,@@      @@@   @@       @@
                        @@@,  @@@      @@    @@      @@#
                       @@      @@      @@     @       @@
                       @@(      @@@@@@@@@@@@           @@
                      @@@@@    @@             @@@@     @@
                      @@ @@@    @@               .@@@  *@@
                      @@   @@    @@@@@%              @@@@@
                      @@     @@@@#     *@@@@@          @@@
                      @@*                  @@@          @@
                      /@@                @@@            %@@
                       @@               @@              /@@
                       @@@             @@               @@.
                        @@@            @                @@
                          @@                           @@
                           @@@                       @@@
                              @@@@               @@@@
                                  @@@@@@@@@@@@@@&
"""
