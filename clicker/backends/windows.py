# clicker/backends/windows.py
import pyautogui
import ctypes

class WindowsBackend:
    def __init__(self):
        # Disable pyautogui's internal failsafe
        pyautogui.FAILSAFE = False

        # Force Windows to treat pyautogui consistently
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    def click(self, x: int, y: int):
        pyautogui.moveTo(int(x), int(y), duration=0)
        pyautogui.mouseDown()
        pyautogui.mouseUp()
