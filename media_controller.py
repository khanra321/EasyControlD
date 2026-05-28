import ctypes
import win32con
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc

class MediaController:
    """Handle media commands and system volume/brightness with original robust logic."""

    APPCOMMAND_PLAY_PAUSE = 14
    APPCOMMAND_NEXT_TRACK = 11
    APPCOMMAND_PREVIOUS_TRACK = 12
    WM_APPCOMMAND = 0x0319
    HWND_BROADCAST = 0xFFFF

    @staticmethod
    def _send_input_key(key_code):
        try:
            ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", ctypes.c_ushort),
                    ("wScan", ctypes.c_ushort),
                    ("dwFlags", ctypes.c_ulong),
                    ("time", ctypes.c_ulong),
                    ("dwExtraInfo", ULONG_PTR),
                ]

            class INPUT(ctypes.Structure):
                _fields_ = [
                    ("type", ctypes.c_ulong),
                    ("ki", KEYBDINPUT),
                ]

            INPUT_KEYBOARD = 1
            KEYEVENTF_KEYUP = 0x0002
            KEYEVENTF_EXTENDEDKEY = 0x0001

            extra = ULONG_PTR(0)
            inp = INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=key_code,
                    wScan=0,
                    dwFlags=KEYEVENTF_EXTENDEDKEY,
                    time=0,
                    dwExtraInfo=extra,
                ),
            )

            if ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp)) == 0:
                return False

            inp.ki.dwFlags = KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP
            if ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp)) == 0:
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def send_media_key(key_code):
        return MediaController._send_input_key(key_code)

    @staticmethod
    def send_appcommand(command):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            lparam = command << 16
            if hwnd:
                ctypes.windll.user32.SendMessageW(hwnd, 0x0319, hwnd, lparam)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def send_broadcast_appcommand(command):
        try:
            lparam = command << 16
            ctypes.windll.user32.SendMessageW(
                0xFFFF,
                0x0319,
                0,
                lparam,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def play_pause():
        if MediaController.send_media_key(win32con.VK_MEDIA_PLAY_PAUSE):
            return True
        if MediaController.send_appcommand(14):
            return True
        return MediaController.send_broadcast_appcommand(14)

    @staticmethod
    def next_track():
        if MediaController.send_media_key(win32con.VK_MEDIA_NEXT_TRACK):
            return True
        if MediaController.send_appcommand(11):
            return True
        if MediaController.send_broadcast_appcommand(11):
            return True
        return False

    @staticmethod
    def previous_track():
        if MediaController.send_media_key(win32con.VK_MEDIA_PREV_TRACK):
            return True
        if MediaController.send_appcommand(12):
            return True
        if MediaController.send_broadcast_appcommand(12):
            return True
        return False

    @staticmethod
    def set_volume(percent):
        try:
            percent = max(0, min(100, int(percent)))
            from ctypes import cast, POINTER
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            min_vol, max_vol, _ = volume.GetVolumeRange()
            vol_db = min_vol + (max_vol - min_vol) * (percent / 100.0)
            volume.SetMasterVolumeLevel(vol_db, None)
            return True
        except Exception:
            return False

    @staticmethod
    def set_brightness(percent):
        try:
            percent = max(0, min(100, int(percent)))
            sbc.set_brightness(percent)
            return True
        except Exception:
            return False
