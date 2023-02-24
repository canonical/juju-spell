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

"""JujuSpell cli commands."""
from .add_user import AddUserCMD
from .enable_user import EnableUserCMD
from .grant import GrantCMD
from .ping import PingCMD
from .remove_user import RemoveUserCMD
from .show_controller import ShowControllerInformationCMD
from .status import StatusCMD
from .update_packages import UpdatePackages

__all__ = [
    "AddUserCMD",
    "EnableUserCMD",
    "GrantCMD",
    "RemoveUserCMD",
    "PingCMD",
    "StatusCMD",
    "ShowControllerInformationCMD",
    "UpdatePackages",
]
