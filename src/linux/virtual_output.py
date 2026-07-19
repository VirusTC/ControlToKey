# /src/linux/virtual_output.py
import uinput

class LinuxVirtualOutputDriver:
    def __init__(self):
        # High fidelity Windows Virtual Key (VK) conversion mapping layout
        self.vk_map = {
            0x08: uinput.KEY_BACKSPACE,
            0x09: uinput.KEY_TAB,
            0x0D: uinput.KEY_ENTER,
            0x10: uinput.KEY_LEFTSHIFT,
            0x11: uinput.KEY_LEFTCTRL,
            0x12: uinput.KEY_LEFTALT,
            0x1B: uinput.KEY_ESC,
            0x20: uinput.KEY_SPACE,
            0x25: uinput.KEY_LEFT,
            0x26: uinput.KEY_UP,
            0x27: uinput.KEY_RIGHT,
            0x28: uinput.KEY_DOWN,
            # Complete sequential index for Alphanumerics
            **{ord(c): getattr(uinput, f"KEY_{c}") for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
        }
        self.active_keys = set()
        self.device = None
        self._create_uinput_device()

    def _create_uinput_device(self):
        # Register keys, relative mouse axes, and directional scroll-wheels
        registered_events = list(self.vk_map.values()) + [
            uinput.REL_X,
            uinput.REL_Y,
            uinput.REL_WHEEL,
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT
        ]
        self.device = uinput.Device(registered_events, name="ControlToKey-InputEngine")

    def press_key(self, vk_code):
        key = self.vk_map.get(vk_code)
        if key and key not in self.active_keys:
            self.device.emit(key, 1)
            self.active_keys.add(key)

    def release_key(self, vk_code):
        key = self.vk_map.get(vk_code)
        if key and key in self.active_keys:
            self.device.emit(key, 0)
            self.active_keys.discard(key)

    def move_mouse(self, x, y):
        if x != 0: self.device.emit(uinput.REL_X, x)
        if y != 0: self.device.emit(uinput.REL_Y, y)

    def scroll_mouse(self, vertical_clicks):
        # JoyToKey positive values scroll upward, negative values scroll downward
        self.device.emit(uinput.REL_WHEEL, 1 if vertical_clicks > 0 else -1)

    def release_all(self):
        """Prevents persistent stuck key states across cross-profile layer shifting resets."""
        for key in list(self.active_keys):
            self.device.emit(key, 0)
        self.active_keys.clear()
