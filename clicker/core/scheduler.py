# clicker/core/scheduler.py
import time
import threading


class ClickScheduler:
    def __init__(self, target_ts: float, callback):
        self.target_ts = target_ts
        self.callback = callback
        self._stop = threading.Event()

    def start(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def cancel(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            now = time.time()
            if now >= self.target_ts:
                self.callback()
                return
            time.sleep(min(0.001, self.target_ts - now))
