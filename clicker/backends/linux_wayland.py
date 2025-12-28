# clicker/platform/linux_wayland.py
import subprocess
from clicker.core.interfaces import ClickBackend


class LinuxWaylandBackend(ClickBackend):
    def click(self, x: int, y: int):
        subprocess.run(["ydotool", "mousemove", str(x), str(y)], check=False)
        subprocess.run(["ydotool", "click", "1"], check=False)
