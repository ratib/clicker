# clicker/core/logger.py
from datetime import datetime


class Logger:
    def __init__(self):
        self.lines = []

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"[{ts}] {msg}"
        self.lines.append(line)
        return line
