"""Import this library to use connect manager."""

from .manager import ConnectManager

__all__ = ["connect_manager", "get_controller"]

connect_manager: ConnectManager = ConnectManager()
get_controller = connect_manager.get_controller
