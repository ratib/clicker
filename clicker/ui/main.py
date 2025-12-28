# clicker/ui/main.py
from datetime import datetime, timedelta
import sys
import time
import platform as pf

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QTextEdit, QTimeEdit, QFrame
)
from PySide6.QtCore import Qt, QTime, QTimer, QMetaObject, Slot
from PySide6.QtGui import QCursor, QFont

from clicker.core.scheduler import ClickScheduler
from clicker.core.logger import Logger

# Let Qt handle DPI awareness (DO NOT force it manually)

if pf.system() == "Windows":
    from clicker.backends.windows import WindowsBackend
    backend = WindowsBackend()
elif pf.system() == "Darwin":
    from clicker.backends.macos import MacOSBackend
    backend = MacOSBackend()
else:
    raise RuntimeError("Only Windows and macOS supported")


class CaptureOverlay(QWidget):
    def __init__(self, callback):
        super().__init__(None)
        self.callback = callback

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.setWindowOpacity(0.01)
        self.setCursor(Qt.CrossCursor)

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())

        self.show()
        self.raise_()
        self.activateWindow()
        self.grabMouse()

        print("Overlay shown and mouse grabbed")

    def mousePressEvent(self, event):
        pos = QCursor.pos()
        print("Overlay click captured:", pos.x(), pos.y())

        self.releaseMouse()
        self.callback(pos.x(), pos.y())
        self.close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.logger = Logger()
        self.scheduler = None
        self.x = None
        self.y = None

        self.setWindowTitle("Precise Clicker")
        self.setFixedWidth(250)

        big = QFont("Consolas", 28, QFont.Bold)
        mid = QFont("Consolas", 18, QFont.Bold)

        self.current_time_label = QLabel("00:00:00")
        self.current_time_label.setFont(big)
        self.current_time_label.setAlignment(Qt.AlignCenter)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFont(mid)
        self.time_edit.setKeyboardTracking(False)
        self.time_edit.setAlignment(Qt.AlignCenter)

        self.capture_btn = QPushButton("Capture Click Position")
        self.capture_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.pos_label = QLabel("X: -, Y: -")
        self.pos_label.setAlignment(Qt.AlignCenter)

        self.countdown = QLabel("00:00:00.000")
        self.countdown.setFont(mid)
        self.countdown.setAlignment(Qt.AlignCenter)
        self.countdown.setStyleSheet("color: #d32f2f;")

        self.arm_btn = QPushButton("START CLICKER")
        self.arm_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet("font-weight: bold; padding: 6px;")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(100)
        self.log_view.setStyleSheet("font-size: 10px; color: #444;")

        self.footer = QLabel("developer: ratib1988@gmail.com")
        self.footer.setAlignment(Qt.AlignCenter)        
        self.footer.setStyleSheet("font-size: 9px; color: gray;")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Current System Time", alignment=Qt.AlignCenter))
        layout.addWidget(self.current_time_label)
        layout.addSpacing(15)

        layout.addWidget(self.capture_btn)
        layout.addWidget(self.pos_label)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Target Click Time", alignment=Qt.AlignCenter))
        layout.addWidget(self.time_edit)
        layout.addSpacing(15)

        layout.addWidget(self.arm_btn)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Time Remaining", alignment=Qt.AlignCenter))
        layout.addWidget(self.countdown)
        layout.addSpacing(15)

        
        layout.addWidget(self.cancel_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        layout.addWidget(self.log_view)
        layout.addWidget(self.footer)

        self.capture_btn.clicked.connect(self.start_capture)
        self.arm_btn.clicked.connect(self.arm)
        self.cancel_btn.clicked.connect(self.cancel)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(50)

    def start_capture(self):
        self._overlay = CaptureOverlay(self.on_captured)

    def on_captured(self, x, y):
        self.x, self.y = x, y
        self.pos_label.setText(f"X: {x}, Y: {y}")
        self.log_view.append(self.logger.log(f"Captured ({x},{y})"))

    def arm(self):
        if self.x is None or self.y is None:
            self.log_view.append(self.logger.log("ERROR: position not set"))
            return

        if self.scheduler:
            self.scheduler.cancel()

        now = datetime.now()
        t = self.time_edit.time()

        target = now.replace(
            hour=t.hour(),
            minute=t.minute(),
            second=t.second(),
            microsecond=t.msec() * 1000
        )

        if (now - target).total_seconds() > 2:
            target += timedelta(days=1)

        self.scheduler = ClickScheduler(
            target.timestamp(),
            self._schedule_click
        )
        self.scheduler.start()
        self.log_view.append(
            self.logger.log(
                f"Clicker Started for {target.strftime('%H:%M:%S.%f')[:-3]}"
            )
        )

    def _schedule_click(self):
        QMetaObject.invokeMethod(
            self, "_execute_click_main", Qt.QueuedConnection
        )

    @Slot()
    def _execute_click_main(self):
        backend.click(self.x, self.y)
        self.log_view.append(self.logger.log("Click executed"))
        self.scheduler = None

    def cancel(self):
        if self.scheduler:
            self.scheduler.cancel()
            self.scheduler = None
            self.log_view.append(self.logger.log("Clicker canceled"))

    def update_countdown(self):
        self.current_time_label.setText(QTime.currentTime().toString("HH:mm:ss"))

        if not self.scheduler:
            return

        remaining = self.scheduler.target_ts - time.time()
        if remaining < 0:
            remaining = 0

        ms = int((remaining % 1) * 1000)
        s = int(remaining) % 60
        m = (int(remaining) // 60) % 60
        h = int(remaining) // 3600

        self.countdown.setText(f"{h:02}:{m:02}:{s:02}.{ms:03}")


app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())
