# /src/linux/device_listener.py
import os
import evdev
from evdev import ecodes

class LinuxGamepadEngine:
    def __init__(self, default_profile_name, parsed_profiles, device_path=None):
        self.profiles = parsed_profiles
        self.base_profile_name = default_profile_name
        self.current_profile_name = default_profile_name
        self.active_profile = self.profiles.get(default_profile_name)
        
        # Automatically fallback look up for standard F310 Event links
        self.device_path = device_path or "/dev/input/by-id/usb-Logitech_Gamepad_F310_-event-joystick"
        if not os.path.exists(self.device_path):
            self.device_path = "/dev/input/event0" # Fallback if specific by-id entry is unlinked
            
        self.pressed_buttons = set()
        self.output_driver = None
        
        # Evdev Logitech F310 Axis Code Maps
        self.axis_map = {
            ecodes.ABS_X: "axis1",   # Left Stick X
            ecodes.ABS_Y: "axis2",   # Left Stick Y
            ecodes.ABS_Z: "axis3",   # Right Stick X
            ecodes.ABS_RZ: "axis4",  # Right Stick Y
        }
        
        # Button ID layout map tracking conversions
        self.btn_map = {
            ecodes.BTN_SOUTH: 1,  # A Button
            ecodes.BTN_EAST: 2,   # B Button
            ecodes.BTN_NORTH: 3,  # X Button
            ecodes.BTN_WEST: 4,   # Y Button
            ecodes.BTN_TL: 5,     # L1 LB
            ecodes.BTN_TR: 6,     # R1 RB
            ecodes.BTN_TL2: 7,    # L2 LT
            ecodes.BTN_TR2: 8,    # R2 RT
            ecodes.BTN_SELECT: 9, # Back
            ecodes.BTN_START: 10, # Start
            ecodes.BTN_THUMBL: 11,# Left Stick click
            ecodes.BTN_THUMBR: 12 # Right Stick click
        }

    def bind_output_driver(self, driver):
        self.output_driver = driver

    def start_loop(self):
        if not os.path.exists(self.device_path):
            raise FileNotFoundError(f"Gamepad device target context missing at: {self.device_path}")
            
        device = evdev.InputDevice(self.device_path)
        device.grab() # Exclusively grab inputs so events don't pass into underlying windows
        
        try:
            for event in device.read_loop():
                if event.type == ecodes.EV_KEY and event.code in self.btn_map:
                    self.process_button(self.btn_map[event.code], event.value)
                elif event.type == ecodes.EV_ABS and event.code in self.axis_map:
                    self.process_axis(self.axis_map[event.code], event.value)
        finally:
            try:
                device.ungrab()
            except Exception:
                pass

    def process_button(self, btn_id, is_pressed):
        mapping = self.active_profile["buttons"].get(btn_id)
        
        if is_pressed:
            self.pressed_buttons.add(btn_id)
            if not mapping or not self.output_driver: return
            
            if mapping["type"] == "KEYBOARD":
                for key in mapping["keys"]:
                    self.output_driver.press_key(key)
            elif mapping["type"] == "PROFILE_SHIFT":
                target = mapping["target"]
                if target in self.profiles:
                    self.current_profile_name = target
                    self.active_profile = self.profiles[target]
                    print(f"[*] Profile Shift Layer Active -> [{target}]")
        else:
            if btn_id in self.pressed_buttons:
                self.pressed_buttons.remove(btn_id)
            if not mapping or not self.output_driver: return
            
            if mapping["type"] == "KEYBOARD":
                for key in mapping["keys"]:
                    self.output_driver.release_key(key)
            elif mapping["type"] == "PROFILE_SHIFT":
                self.current_profile_name = self.base_profile_name
                self.active_profile = self.profiles[self.base_profile_name]
                self.output_driver.release_all()
                print(f"[*] Profile Shift Layer Reverted -> [{self.base_profile_name}]")

    def process_axis(self, axis_name, raw_value):
        threshold = self.active_profile.get("threshold", 4000)
        
        # Centering neutral value calculations (F310 outputs typical -32768 to 32767 ranges)
        if abs(raw_value) <= threshold:
            # We are within deadzone: issue clear instructions
            self._execute_axis_action(axis_name, 'n', 0.0)
            self._execute_axis_action(axis_name, 'p', 0.0)
            return

        direction_suffix = 'n' if raw_value < 0 else 'p'
        max_range = 32768 - threshold
        pressure_ratio = (abs(raw_value) - threshold) / max_range
        
        # Clamp absolute scale boundary limits securely
        pressure_ratio = max(0.0, min(1.0, pressure_ratio))
        
        self._execute_axis_action(axis_name, direction_suffix, pressure_ratio)

    def _execute_axis_action(self, axis_name, suffix, pressure_ratio):
        lookup_key = f"{axis_name}{suffix}"
        mapping = self.active_profile["axes"].get(lookup_key)
        
        if not mapping or not self.output_driver:
            return
            
        if mapping["type"] == "MOUSE":
            if pressure_ratio > 0:
                mx = int(mapping["x"] * pressure_ratio)
                my = int(mapping["y"] * pressure_ratio)
                if mx != 0 or my != 0:
                    self.output_driver.move_mouse(mx, my)
                if mapping["wheel"] != 0:
                    self.output_driver.scroll_mouse(mapping["wheel"])
        elif mapping["type"] == "KEYBOARD":
            if pressure_ratio > 0:
                for key in mapping["keys"]:
                    self.output_driver.press_key(key)
            else:
                for key in mapping["keys"]:
                    self.output_driver.release_key(key)
