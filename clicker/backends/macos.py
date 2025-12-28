# clicker/platform/macos.py
from clicker.core.interfaces import ClickBackend
import Quartz


class MacOSBackend(ClickBackend):
    def click(self, x: int, y: int):
        down = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDown, (x, y), Quartz.kCGMouseButtonLeft
        )
        up = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseUp, (x, y), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
