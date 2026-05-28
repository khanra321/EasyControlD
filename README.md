# 🤟 EasyControlD - Gesture-Based PC Controller

**EasyControlD** is a professional desktop application designed to provide a touchless experience for controlling your PC. Using advanced Hand Gesture Recognition (OpenCV & MediaPipe), you can manage system volume, screen brightness, and media playback simply by moving your hands in front of your camera.

---

## Key Features

- **Intuitive Volume Control:** Adjust system volume using your **Right Hand**.
- **Smart Brightness Control:** Adjust screen brightness using your **Left Hand**.
- **Advanced Media Playback:** Play or Pause music/videos with a specialized "Armed OK" gesture.
- **Track Navigation:** Skip to the Next or Previous track with simple finger movements.
- **Visual Feedback:** Real-time on-screen overlay messages for every action.
- **Modular & High Performance:** Refactored into a professional multi-file structure for low latency and high readability.
- **Dual Camera Support:** Seamlessly switch between Laptop and External/Phone cameras (supports DroidCam/Iriun).
- **Background Mode:** Runs quietly in the system tray with shortcut support (`S`, `P`, `Q`).

---

## Gesture Guide

| Action | Hand | Gesture Description |
| :--- | :--- | :--- |
| **Volume Up/Down** | **Right** | Raise **Pinky** and **Index** fingers. Move **Thumb** and **Index** closer/apart to adjust. |
| **Brightness Control** | **Left** | Raise **Pinky** and **Index** fingers. Move **Thumb** and **Index** closer/apart to adjust. |
| **Play / Pause** | Either | 1. Make an **OK sign** (Thumb+Index).<br>2. Hold other fingers **UP** to Arm.<br>3. Fold Middle/Ring fingers **DOWN** to Trigger. |
| **Next Track** | **Right** | Raise **Index and Middle** fingers with a gap. Keep others folded. |
| **Previous Track** | **Left** | Raise **Index and Middle** fingers with a gap. Keep others folded. |

---

## Installation & Setup

### 1. Clone or Download
Download the project files to your local machine.

### 2. Install Dependencies
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the service using:
```bash
python upvb_simple.py
```

---

## Building the Desktop App (.exe)

This project includes a dedicated build script to create a standalone, lag-free executable with its own icon.

1. Open **Terminal** or **CMD**.
2. Run the build script:
   ```bash
   python build_app.py
   ```
3. Once completed, your app will be ready in the **`dist`** folder as `EasyControlD.exe`.

---

## Tech Stack

- **Python**: Core application logic.
- **MediaPipe**: Real-time hand landmark detection.
- **OpenCV**: Computer vision and camera feed processing.
- **PyQt5**: Professional and responsive GUI.
- **Pywin32 / Pycaw**: Advanced Windows system and audio integration.
- **PyInstaller**: Application bundling and optimization.

---

## Author

- **Name:** Akash Khanra
- **GitHub:** [@khanra321](https://github.com/khanra321)


