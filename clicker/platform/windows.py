# clicker/platform/windows.py
import ctypes
from clicker.core.interfaces import ClickBackend

user32 = ctypes.windll.user32


class WindowsBackend(ClickBackend):
    def click(self, x: int, y: int):
        user32.SetCursorPos(x, y)
        user32.mouse_event(2, 0, 0, 0, 0)
        user32.mouse_event(4, 0, 0, 0, 0)
