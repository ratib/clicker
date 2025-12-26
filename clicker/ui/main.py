# clicker/ui/main.py
from datetime import datetime, timedelta

import sys
import time
import platform as pf
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QTextEdit, QTimeEdit, QFrame
)
from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QCursor, QFont
from clicker.core.scheduler import ClickScheduler
from clicker.core.logger import Logger

if pf.system() == "Windows":
    from clicker.platform.windows import WindowsBackend
    backend = WindowsBackend()
elif pf.system() == "Darwin":
    from clicker.platform.macos import MacOSBackend
    backend = MacOSBackend()
else:
    from clicker.platform.linux_wayland import LinuxWaylandBackend
    backend = LinuxWaylandBackend()


class CaptureOverlay(QWidget):
    def __init__(self, callback):
        super().__init__(None)
        self.callback = callback

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        # IMPORTANT: do NOT rely on transparency for input
        self.setWindowOpacity(0.01)

        self.setCursor(Qt.CrossCursor)

        screen = QApplication.primaryScreen()
        self.setGeometry(screen.virtualGeometry())

        self.show()
        self.raise_()
        self.activateWindow()

        # 🔑 THIS IS THE KEY LINE
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
        big_time_font = QFont("Consolas")
        big_time_font.setPointSize(28)
        big_time_font.setBold(True)

        medium_time_font = QFont("Consolas")
        medium_time_font.setPointSize(18)
        medium_time_font.setBold(True)

        self.logger = Logger()
        self.scheduler = None
        self.x = None
        self.y = None

        self.setWindowTitle("Precise Clicker")
        self.setFixedWidth(360)

        mono = QFont("Consolas")
        mono.setPointSize(11)

        self.current_time_label = QLabel("00:00:00")
        self.current_time_label.setFont(big_time_font)
        self.current_time_label.setAlignment(Qt.AlignCenter)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss.zzz")
        self.time_edit.setTime(QTime.currentTime())
        self.time_edit.setFont(medium_time_font)

        # IMPORTANT: prevent invalid typing
        self.time_edit.setKeyboardTracking(False)
        self.time_edit.setWrapping(True)
        self.time_edit.setButtonSymbols(QTimeEdit.UpDownArrows)

        self.capture_btn = QPushButton("Capture Click Position")
        self.pos_label = QLabel("X: -, Y: -")

        self.countdown = QLabel("00:00:00.000")
        self.countdown.setFont(medium_time_font)
        self.countdown.setAlignment(Qt.AlignCenter)
        self.countdown.setStyleSheet("color: #d32f2f;")  # red for urgency

        self.arm_btn = QPushButton("ARM CLICK")
        self.arm_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setStyleSheet("padding: 6px;")

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(150)
        self.log_view.setStyleSheet("font-size: 10px; color: #444;")

        self.footer = QLabel("developer: ratib1988@gmail.com")
        self.footer.setAlignment(Qt.AlignCenter)        
        self.footer.setStyleSheet("font-size: 9px; color: gray;")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Current System Time", alignment=Qt.AlignCenter))
        layout.addWidget(self.current_time_label)
        layout.addSpacing(15)

        layout.addWidget(QLabel("Target Click Time", alignment=Qt.AlignCenter))
        layout.addWidget(self.time_edit)
        layout.addSpacing(15)

        layout.addWidget(self.capture_btn)
        layout.addWidget(self.pos_label)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Time Remaining", alignment=Qt.AlignCenter))
        layout.addWidget(self.countdown)
        layout.addSpacing(15)


        layout.addWidget(self.arm_btn)
        layout.addWidget(self.cancel_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        layout.addWidget(self.log_view)
        layout.addWidget(self.footer)
        self.setLayout(layout)

        self.capture_btn.clicked.connect(self.start_capture
        )
        self.arm_btn.clicked.connect(self.arm)
        self.cancel_btn.clicked.connect(self.cancel)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(50)

    def start_capture(self):
        print("start_capture() called")
        self._overlay = CaptureOverlay(self.on_captured)




    def on_captured(self, x, y):
        self.x, self.y = x, y
        self.pos_label.setText(f"X: {x}, Y: {y}")
        self.log_view.append(self.logger.log(f"Position captured ({x},{y})"))
        self._overlay = None



    def arm(self):
        if self.x is None or self.y is None:
            self.log_view.append(self.logger.log("ERROR: Click position not set"))
            return

        now = datetime.now()
        t = self.time_edit.time()

        target = now.replace(
            hour=t.hour(),
            minute=t.minute(),
            second=t.second(),
            microsecond=t.msec() * 1000
        )

        # If target already passed today, schedule for tomorrow
        if target <= now:
            target += timedelta(days=1)

        self.scheduler = ClickScheduler(target.timestamp(), self.execute_click)
        self.scheduler.start()

        self.log_view.append(
            self.logger.log(
                f"Click armed for {target.strftime('%H:%M:%S.%f')[:-3]}"
            )
        )


    def cancel(self):
        if self.scheduler:
            self.scheduler.cancel()
            self.scheduler = None
            self.log_view.append(self.logger.log("Click canceled"))

    def update_countdown(self):
        now_qt = QTime.currentTime()
        self.current_time_label.setText(now_qt.toString("HH:mm:ss"))

        if not self.scheduler:
            return

        remaining = self.scheduler.target_ts - time.time()
        if remaining < 0:
            remaining = 0

        ms = int((remaining - int(remaining)) * 1000)
        s = int(remaining) % 60
        m = (int(remaining) // 60) % 60
        h = int(remaining) // 3600

        self.countdown.setText(f"{h:02}:{m:02}:{s:02}.{ms:03}")


    def execute_click(self):
        backend.click(self.x, self.y)
        self.log_view.append(self.logger.log("Click executed"))
        self.scheduler = None


app = QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec())
