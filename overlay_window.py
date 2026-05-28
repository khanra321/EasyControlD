from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QApplication

class OverlayWindow(QWidget):
    """Floating overlay window for feedback messages."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 90)

        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            """
            QLabel {
                color: white;
                background-color: rgba(0, 0, 0, 180);
                border: 2px solid white;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
            }
            """
        )

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.hide()
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def showMessage(self, text, duration=1200):
        """Display a temporary overlay message centered above the app."""
        self.label.setText(text)
        self.updatePosition()
        self.show()
        self.hide_timer.stop()
        self.hide_timer.start(duration)

    def updatePosition(self):
        screen = QApplication.primaryScreen().geometry()
        target_x = screen.width() // 2 - self.width() // 2
        target_y = 140
        self.move(target_x, target_y)
