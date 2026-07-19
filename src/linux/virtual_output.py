# src/linux/virtual_output.py
import uinput

class LinuxVirtualOutputDriver:
    def __init__(self):
        # Full registration schema matching the Windows Virtual Key layout targets
        self.vk_to_uinput = {
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
            # Alphanumerics mapping index
            **{ord(c): getattr(uinput, f"KEY_{c}") for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
        }
        self.device = None
        self.active_keys = set()
        self._initialize_device()

    def _initialize_device(self):
        # Register keys, relative mouse motion axes, and vertical wheels
        events = list(self.vk_to_uinput.values()) + [
            uinput.REL_X,
            uinput.REL_Y,
            uinput.REL_WHEEL,
            uinput.BTN_LEFT,
            uinput.BTN_RIGHT
        ]
        self.device = uinput.Device(events, name="ControlToKey-Virtual-Pipeline")

    def press_key(self, vk_code):
        linux_key = self.vk_to_uinput.get(vk_code)
        if linux_key:
            self.device.emit(linux_key, 1)
            self.active_keys.add(linux_key)

    def release_key(self, vk_code):
        linux_key = self.vk_to_uinput.get(vk_code)
        if linux_key and linux_key in self.active_keys:
            self.device.emit(linux_key, 0)
            self.active_keys.discard(linux_key)

    def move_mouse(self, x, y):
        if x != 0:
            self.device.emit(uinput.REL_X, x)
        if y != 0:
            self.device.emit(uinput.REL_Y, y)

    def scroll_mouse(self, click_direction):
        # JoyToKey encodes upward wheels as positive, downward as negative increments
        self.device.emit(uinput.REL_WHEEL, 1 if click_direction > 0 else -1)

    def release_all(self):
        """Safety reset step executed during layer shifting swaps to isolate triggers."""
        for linux_key in list(self.active_keys):
            self.device.emit(linux_key, 0)
        self.active_keys.clear()
