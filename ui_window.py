import re
import time
import os
import sys
from collections import deque
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import (QAction, QFrame, QHBoxLayout, QLabel,
                             QMainWindow, QMenu, QPushButton, QScrollArea, QStyle,
                             QSystemTrayIcon, QVBoxLayout, QWidget)

# Importing modules
from gesture_detector import GestureDetector
from media_controller import MediaController
from camera_thread import CameraThread
from overlay_window import OverlayWindow

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class UpVBDesktop(QMainWindow):
    """Main desktop window with 100% ORIGINAL UI and fixed Camera Switching."""

    def __init__(self):
        super().__init__()
        self.detector = GestureDetector()
        self.controller = MediaController()
        self.camera_thread = None
        self.overlay = OverlayWindow()

        # Exact original logic values
        self.last_volume_level = None
        self.last_brightness_level = None
        self.volume_last_update = 0.0
        self.brightness_last_update = 0.0
        self.volume_update_interval = 0.05
        self.brightness_update_interval = 0.08
        self.volume_values = deque(maxlen=3)
        self.brightness_values = deque(maxlen=3)

        self.preferred_camera_index = 0
        
        # Set Window Icon
        self.setWindowIcon(QIcon(resource_path("gesture.png")))

        self.init_ui()
        self.init_tray()

    def create_guide_card(self, title, icon, details, accent):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: #111b2f; border: 1px solid #24334d; border-radius: 18px; }}"
        )
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(8)

        title_label = QLabel(f"<span style='font-size:13pt; font-weight:800; color:{accent};'>{icon} {title}</span>")
        title_label.setTextFormat(Qt.RichText)
        title_label.setWordWrap(True)

        detail_label = QLabel(details)
        detail_label.setTextFormat(Qt.RichText)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("color: #c3d1eb; font-size: 10pt; line-height: 1.4;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(detail_label)
        card.setLayout(card_layout)
        return card

    def init_ui(self):
        self.setWindowTitle("EasyControlD")
        self.resize(600, 750)
        self.setStyleSheet("background-color: #080b14; color: white;")

        main_content = QWidget()
        layout = QVBoxLayout(main_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        title = QLabel("EasyControlD")
        title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        title.setStyleSheet("color: #3c8cff; margin: 0;")

        subtitle = QLabel("Gesture service ready to control volume, brightness, and media")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet("color: #9fb4df; margin-top: 4px;")
        subtitle.setWordWrap(True)

        header_layout = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header_layout.addLayout(header_text)
        header_layout.addStretch()

        app_icon = QLabel()
        pixmap = QPixmap(resource_path("gesture.png"))
        if not pixmap.isNull():
            app_icon.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            app_icon.setText("🤟")
            app_icon.setFont(QFont("Segoe UI Emoji", 36))
        header_layout.addWidget(app_icon)

        # Status area
        self.status_label = QLabel("Service: Ready")
        self.status_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.status_label.setStyleSheet("color: #f1f5fc;")

        self.camera_source_label = QLabel("Source: Laptop Camera")
        self.camera_source_label.setStyleSheet("color: #3c8cff; font-weight: bold; font-size: 11pt;")

        self.usage_label = QLabel(
            "Activate the service to control your PC with hand gestures. "
            "Use the button below or press 'P' to switch camera."
        )
        self.usage_label.setWordWrap(True)
        self.usage_label.setStyleSheet("color: #b8c6e2; font-size: 10pt;")

        # Buttons
        self.start_btn = QPushButton("ACTIVATE")
        self.start_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet(
            "QPushButton { background-color: #16c166; color: black; border-radius: 20px; padding: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #2be686; }"
        )
        self.start_btn.clicked.connect(self.start_service)

        self.switch_btn = QPushButton("SWITCH CAMERA")
        self.switch_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.switch_btn.setCursor(Qt.PointingHandCursor)
        self.switch_btn.setStyleSheet(
            "QPushButton { background-color: #3c8cff; color: white; border-radius: 20px; padding: 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #5aa1ff; }"
        )
        self.switch_btn.clicked.connect(self.switch_camera)

        self.stop_btn = QPushButton("DEACTIVATE")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #fa5f63; color: white; border-radius: 20px; padding: 16px; font-weight: bold; }"
            "QPushButton:hover:enabled { background-color: #ff7b80; }"
            "QPushButton:disabled { background-color: #37425b; }"
        )
        self.stop_btn.clicked.connect(self.stop_service)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.switch_btn)
        btn_layout.addWidget(self.stop_btn)

        status_card = QFrame()
        status_card.setStyleSheet("QFrame { background-color: #111729; border-radius: 24px; border: 1px solid rgba(255,255,255,0.05); }")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(20, 20, 20, 20)
        sc_layout.addWidget(self.status_label)
        sc_layout.addWidget(self.camera_source_label)
        sc_layout.addWidget(self.usage_label)
        sc_layout.addLayout(btn_layout)

        # Guides section - Exact Original Text
        guide_title = QLabel("Gesture Guide")
        guide_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        guide_title.setStyleSheet("color: #f4f8ff; margin-top: 10px; margin-bottom: 5px;")

        vol_card = self.create_guide_card(
            "Volume & Brightness", "🔊",
            "<ol><li>Raise <b>Pinky (Little)</b> and <b>Index</b> fingers.</li>"
            "<li>Keep Middle and Ring fingers folded.</li>"
            "<li>Move Thumb and Index closer/apart to control.</li>"
            "<li><b>RIGHT Hand:</b> Volume | <b>LEFT Hand:</b> Brightness.</li></ol>",
            "#f8c250"
        )
        media_card = self.create_guide_card(
            "Play / Pause", "▶️",
            "<ol><li>Make an <b>OK sign</b> (Thumb + Index touching).</li>"
            "<li>Hold Middle, Ring and Pinky fingers <b>UP</b> to arm.</li>"
            "<li>Fold Middle and Ring fingers <b>DOWN</b> to trigger.</li></ol>",
            "#c17aff"
        )
        next_prev_card = self.create_guide_card(
            "Next / Previous Track", "⏭️",
            "<ol><li><b>Index and Middle</b> fingers up with a gap.</li>"
            "<li>Keep Thumb, Ring and Pinky fingers folded.</li>"
            "<li><b>Right Hand:</b> Next | <b>Left Hand:</b> Previous.</li></ol>",
            "#3cd4ff"
        )

        layout.addLayout(header_layout)
        layout.addWidget(status_card)
        layout.addWidget(guide_title)
        layout.addWidget(vol_card)
        layout.addWidget(media_card)
        layout.addWidget(next_prev_card)
        layout.addStretch()

        shortcut_note = QLabel("S: Start/Stop | P: Toggle Camera | Q: Quit")
        shortcut_note.setAlignment(Qt.AlignCenter)
        shortcut_note.setStyleSheet("color: #a8b6d3; font-size: 10pt; margin-top: 10px;")
        layout.addWidget(shortcut_note)

        # Scroll Area with original styling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(main_content)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: #080b14; }
            QScrollBar:vertical { border: none; background: #080b14; width: 10px; }
            QScrollBar::handle:vertical { background: #1f2937; min-height: 20px; border-radius: 5px; }
            QScrollBar::handle:vertical:hover { background: #3c8cff; }
        """)
        self.setCentralWidget(scroll)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("gesture.png")))
        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.showNormal)
        exit_action = QAction("Quit", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def start_service(self):
        if self.camera_thread is None:
            self.camera_thread = CameraThread(self.detector, self.preferred_camera_index)
            self.camera_thread.gesture_detected.connect(self.on_gesture)
            self.camera_thread.camera_switched.connect(self.on_camera_switched)
            self.camera_thread.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: #7cff7c;")
        self.setFocus()

    def stop_service(self):
        if self.camera_thread is not None:
            self.camera_thread.stop()
            self.camera_thread.wait()
            self.camera_thread = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: #ff5555;")
        self.setFocus()

    def switch_camera(self):
        """Handle Camera Switch - RESTORED ORIGINAL LOGIC"""
        if self.camera_thread and self.camera_thread.isRunning():
            self.camera_thread.switch_camera()
        else:
            # If not running, toggle the starting index
            self.preferred_camera_index = 0 if self.preferred_camera_index != 0 else 1
            name = "Laptop" if self.preferred_camera_index == 0 else "Phone"
            self.camera_source_label.setText(f"Source: {name} Camera (Selected)")
            self.overlay.showMessage(f"Will start with: {name}")
        self.setFocus()

    def on_camera_switched(self, message):
        """Update UI when camera switch is successful."""
        self.overlay.showMessage(message)
        if "Laptop" in message:
            self.preferred_camera_index = 0
            self.camera_source_label.setText("Source: Laptop Camera")
        else:
            match = re.search(r'Index (\d+)', message)
            self.preferred_camera_index = int(match.group(1)) if match else 1
            self.camera_source_label.setText(f"Source: Phone Camera")

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Q: self.close()
        elif key == Qt.Key_P: self.switch_camera()
        elif key == Qt.Key_S:
            self.start_service() if self.camera_thread is None else self.stop_service()
        else: super().keyPressEvent(event)

    def on_gesture(self, gesture, value, hand):
        current_time = time.time()
        if gesture == 'VOLUME':
            self.volume_values.append(value)
            if current_time - self.volume_last_update >= self.volume_update_interval:
                vol = max(0, min(100, int(round((sum(self.volume_values)/len(self.volume_values)) * 100))))
                if vol != self.last_volume_level:
                    self.controller.set_volume(vol)
                    self.overlay.showMessage(f"🔊 Volume: {vol}%")
                    self.last_volume_level = vol
                self.volume_last_update = current_time
            return
        if gesture == 'BRIGHTNESS':
            self.brightness_values.append(value)
            if current_time - self.brightness_last_update >= self.brightness_update_interval:
                bri = max(0, min(100, int(round((sum(self.brightness_values)/len(self.brightness_values)) * 100))))
                if bri != self.last_brightness_level:
                    self.controller.set_brightness(bri)
                    self.overlay.showMessage(f"☀️ Brightness: {bri}%")
                    self.last_brightness_level = bri
                self.brightness_last_update = current_time
            return

        cooldown = self.detector.next_prev_cooldown if gesture in ['NEXT', 'PREVIOUS'] else self.detector.media_cooldown
        if current_time - self.detector.last_media_action_time < cooldown: return
        self.detector.last_media_action_time = current_time

        if gesture == 'PLAY_PAUSE':
            self.controller.play_pause()
            self.overlay.showMessage('▶️ Play/Pause')
        elif gesture == 'NEXT':
            self.controller.next_track()
            self.overlay.showMessage('⏭️ Next Track')
        elif gesture == 'PREVIOUS':
            self.controller.previous_track()
            self.overlay.showMessage('⏮️ Previous Track')

    def closeEvent(self, event):
        self.stop_service()
        self.overlay.hide()
        event.accept()
