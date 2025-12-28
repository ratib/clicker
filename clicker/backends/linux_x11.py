# clicker/platform/linux_x11.py
import subprocess
from clicker.core.interfaces import ClickBackend


class LinuxX11Backend(ClickBackend):
    def click(self, x: int, y: int):
        subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=False)
        subprocess.run(["xdotool", "click", "1"], check=False)
