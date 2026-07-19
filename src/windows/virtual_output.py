# /src/windows/virtual_output.py
import ctypes
from ctypes import wintypes

# Win32 Structural Definitions for Direct Keyboard & Mouse Injection
MUL = ctypes.sizeof(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("ui", INPUT_UNION)]

# Constants for Windows API SendInput Flags
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800

class WindowsVirtualOutputDriver:
    def __init__(self):
        self.active_keys = set()

    def press_key(self, vk_code):
        if vk_code not in self.active_keys:
            extra = ctypes.c_ulong(0)
            ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=0, time=0, dwExtraInfo=ctypes.pointer(extra))
            ii = INPUT_UNION(ki=ki)
            command = INPUT(type=INPUT_KEYBOARD, ui=ii)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
            self.active_keys.add(vk_code)

    def release_key(self, vk_code):
        if vk_code in self.active_keys:
            extra = ctypes.c_ulong(0)
            ki = KEYBDINPUT(wVk=vk_code, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=ctypes.pointer(extra))
            ii = INPUT_UNION(ki=ki)
            command = INPUT(type=INPUT_KEYBOARD, ui=ii)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
            self.active_keys.discard(vk_code)

    def move_mouse(self, x, y):
        if x != 0 or y != 0:
            extra = ctypes.c_ulong(0)
            mi = MOUSEINPUT(dx=x, dy=y, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=ctypes.pointer(extra))
            ii = INPUT_UNION(mi=mi)
            command = INPUT(type=INPUT_MOUSE, ui=ii)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    def scroll_mouse(self, vertical_clicks):
        if vertical_clicks != 0:
            extra = ctypes.c_ulong(0)
            # JoyToKey uses native wheel factors multiplied by standard scale blocks
            wheel_data = 120 if vertical_clicks > 0 else -120
            mi = MOUSEINPUT(dx=0, dy=0, mouseData=wheel_data, dwFlags=MOUSEEVENTF_WHEEL, time=0, dwExtraInfo=ctypes.pointer(extra))
            ii = INPUT_UNION(mi=mi)
            command = INPUT(type=INPUT_MOUSE, ui=ii)
            ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

    def release_all(self):
        """Prevents persistent stuck keys across cross-profile layer shifting resets."""
        for vk_code in list(self.active_keys):
            self.release_key(vk_code)
        self.active_keys.clear()
