import cv2
import numpy as np
import time
from PyQt5.QtCore import QThread, pyqtSignal

class CameraThread(QThread):
    """Camera loop running in a worker thread with original resolution and timing."""

    gesture_detected = pyqtSignal(str, float, str)
    camera_switched = pyqtSignal(str)

    def __init__(self, detector, start_index=0):
        super().__init__()
        self.detector = detector
        self.running = False
        self.switch_camera_flag = False
        self.current_camera_index = start_index

    def open_camera(self, index):
        """Attempt to open a camera by index and configure a consistent capture size (640x480)."""
        try:
            # Try with DSHOW first (fastest on Windows)
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap or not cap.isOpened():
                # Fallback to default backend
                cap = cv2.VideoCapture(index)

            if cap and cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                return cap
        except Exception:
            pass
        return None

    def run(self):
        """Execute the camera processing loop and emit gesture events to the UI."""
        # Open the initial camera
        current_cam = self.open_camera(self.current_camera_index)

        # Fallback to laptop (0) if preferred fails
        if current_cam is None and self.current_camera_index != 0:
            self.current_camera_index = 0
            current_cam = self.open_camera(0)

        if current_cam is None:
            self.camera_switched.emit("Error: No camera found!")
            return

        self.running = True
        reconnect_attempts = 0
        max_reconnect_attempts = 10

        while self.running:
            if self.switch_camera_flag:
                self.switch_camera_flag = False
                new_cam = None
                target_index = 0
                
                if self.current_camera_index == 0:
                    # Switch TO external/phone camera: try index 1, 2, then 3
                    for idx in [1, 2, 3]:
                        new_cam = self.open_camera(idx)
                        if new_cam:
                            target_index = idx
                            break
                else:
                    # Switch BACK to laptop (index 0)
                    new_cam = self.open_camera(0)
                    target_index = 0

                if new_cam is not None:
                    if current_cam is not None:
                        current_cam.release()
                    current_cam = new_cam
                    self.current_camera_index = target_index
                    cam_name = "Laptop" if target_index == 0 else f"Phone/External (Index {target_index})"
                    self.camera_switched.emit(f"Switched to {cam_name}")
                else:
                    self.camera_switched.emit("Alternative camera not available")
                continue

            ret, frame = current_cam.read()
            if not ret:
                reconnect_attempts += 1
                if reconnect_attempts > max_reconnect_attempts:
                    self.camera_switched.emit("Camera disconnected.")
                    break

                time.sleep(0.2)
                if current_cam is not None:
                    current_cam.release()
                current_cam = self.open_camera(self.current_camera_index)
                continue

            reconnect_attempts = 0
            frame = cv2.flip(frame, 1)

            # Brightness correction logic - EXACT original values
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            mean_brightness = np.mean(gray)
            if mean_brightness < 80:
                alpha = min(2.0, 100.0 / max(mean_brightness, 1.0))
                frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=15)

            gesture, value, hand = self.detector.detect(frame)
            if gesture:
                self.gesture_detected.emit(gesture, value, hand)

            self.msleep(15) # EXACT original sleep timing

        if current_cam is not None:
            current_cam.release()

    def stop(self):
        self.running = False

    def switch_camera(self):
        self.switch_camera_flag = True
