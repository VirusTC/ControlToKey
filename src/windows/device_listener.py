# /src/windows/device_listener.py
import ctypes
import time
from ctypes import wintypes

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_byte),
        ("bRightTrigger", ctypes.c_byte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]

class WindowsGamepadEngine:
    def __init__(self, default_profile_name, parsed_profiles):
        self.profiles = parsed_profiles
        self.base_profile_name = default_profile_name
        self.current_profile_name = default_profile_name
        self.active_profile = self.profiles.get(default_profile_name)
        
        self.pressed_buttons = set()
        self.output_driver = None
        self.running = False
        
        # Track past Hat state to execute discrete press-and-release loops
        self.last_buttons_mask = 0
        
        # XInput Bitmask conversion mappings for Logitech F310 Buttons
        self.btn_mask_map = {
            0x1000: 1,  # A
            0x2000: 2,  # B
            0x4000: 3,  # X
            0x8000: 4,  # Y
            0x0100: 5,  # LB
            0x0200: 6,  # RB
            0x0020: 9,  # BACK
            0x0010: 10, # START
            0x0040: 11, # L3 Click
            0x0080: 12, # R3 Click
        }
        
        # POV D-Pad mapping rules matching standard configurations
        self.pov_map = {
            0x0001: "pov1u", # Up
            0x0002: "pov1d", # Down
            0x0004: "pov1l", # Left
            0x0008: "pov1r", # Right
        }

    def bind_output_driver(self, driver):
        self.output_driver = driver

    def start_loop(self):
        xinput = ctypes.windll.xinput1_4
        state = XINPUT_STATE()
        self.running = True
        
        print("[*] Accessing Direct XInput pipelines. Monitoring for Logitech F310 connectivity...")
        
        while self.running:
            # Query User Index 0 (First plugged controller asset node)
            result = xinput.XInputGetState(0, ctypes.pointer(state))
            
            if result == 0:
                self.process_xinput_state(state.Gamepad)
            elif result == 1167:
                # Device disconnected error fallback log
                time.sleep(2.0)
                continue
                
            # Run loops at roughly ~60Hz to limit background CPU usage
            time.sleep(0.016)

    def process_xinput_state(self, gamepad):
        # 1. Process Standard Face/Functional Buttons
        for mask, btn_id in self.btn_mask_map.items():
            is_down = bool(gamepad.wButtons & mask)
            was_down = btn_id in self.pressed_buttons
            
            if is_down and not was_down:
                self._execute_button_action(btn_id, is_pressed=True)
            elif not is_down and was_down:
                self._execute_button_action(btn_id, is_pressed=False)

        # 2. Process Discrete POV Hat Changes
        for mask, pov_key in self.pov_map.items():
            is_down = bool(gamepad.wButtons & mask)
            was_down = bool(self.last_buttons_mask & mask)
            
            if is_down and not was_down:
                self._execute_axis_action(pov_key, 1.0)
            elif not is_down and was_down:
                self._execute_axis_action(pov_key, 0.0)

        # 3. Process Left Analog Navigation Stick Scaling Metrics
        threshold = self.active_profile.get("threshold", 4000)
        self._handle_analog_axis("axis1", gamepad.sThumbLX, threshold)
        self._handle_analog_axis("axis2", -gamepad.sThumbLY, threshold) # Invert axis coordinate lines to match

        self.last_buttons_mask = gamepad.wButtons

    def _handle_analog_axis(self, axis_base, raw_val, threshold):
        if abs(raw_val) <= threshold:
            self._execute_axis_action(f"{axis_base}n", 0.0)
            self._execute_axis_action(f"{axis_base}p", 0.0)
            return
            
        direction_suffix = 'n' if raw_val < 0 else 'p'
        max_range = 32768 - threshold
        pressure_ratio = (abs(raw_val) - threshold) / max_range
        pressure_ratio = max(0.0, min(1.0, pressure_ratio))
        
        self._execute_axis_action(f"{axis_base}{direction_suffix}", pressure_ratio)

    def _execute_button_action(self, btn_id, is_pressed):
        mapping = self.active_profile["buttons"].get(btn_id)
        if is_pressed:
            self.pressed_buttons.add(btn_id)
            if not mapping or not self.output_driver: return
            
            if mapping["type"] == "KEYBOARD":
                for key in mapping["keys"]: self.output_driver.press_key(key)
            elif mapping["type"] == "PROFILE_SHIFT":
                target = mapping["target"]
                if target in self.profiles:
                    self.active_profile = self.profiles[target]
                    print(f"[*] Window Profile Shift Active -> [{target}]")
        else:
            self.pressed_buttons.discard(btn_id)
            if not mapping or not self.output_driver: return
            
            if mapping["type"] == "KEYBOARD":
                for key in mapping["keys"]: self.output_driver.release_key(key)
            elif mapping["type"] == "PROFILE_SHIFT":
                self.active_profile = self.profiles[self.base_profile_name]
                self.output_driver.release_all()
                print(f"[*] Window Profile Shift Reverted -> [{self.base_profile_name}]")

    def _execute_axis_action(self, lookup_key, pressure_ratio):
        mapping = self.active_profile["axes"].get(lookup_key)
        if not mapping or not self.output_driver: return
        
        if mapping["type"] == "MOUSE":
            if pressure_ratio > 0:
                mx = int(mapping["x"] * pressure_ratio)
                my = int(mapping["y"] * pressure_ratio)
                if mx != 0 or my != 0: self.output_driver.move_mouse(mx, my)
                if mapping["wheel"] != 0: self.output_driver.scroll_mouse(mapping["wheel"])
        elif mapping["type"] == "KEYBOARD":
            if pressure_ratio > 0:
                for key in mapping["keys"]: self.output_driver.press_key(key)
            else:
                for key in mapping["keys"]: self.output_driver.release_key(key)
