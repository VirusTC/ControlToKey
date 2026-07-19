import os
import evdev
from evdev import ecodes
from src.core.state_machine import ActionDispatcher

class LinuxGamepadEngine:
    def __init__(self, device_path="/dev/input/by-id/usb-Logitech_Gamepad_F310_-event-joystick"):
        self.device_path = device_path
        self.dispatcher = ActionDispatcher() # Handles profile shifting & macro queues
        self.axis_states = {ecodes.ABS_X: 0, ecodes.ABS_Y: 0, ecodes.ABS_Z: 0, ecodes.ABS_RZ: 0}
        
    def start_loop(self):
        # Validate that the controller node is accessible
        if not os.path.exists(self.device_path):
            raise FileNotFoundError(f"Logitech F310 not found at {self.device_path}")
            
        device = evdev.InputDevice(self.device_path)
        print(f"ControlToKey binding directly to hardware: {device.name}")
        
        # Exclusive grab so events don't leak double inputs across the OS
        device.grab()
        
        try:
            for event in device.read_loop():
                if event.type == ecodes.EV_KEY:
                    # event.code = Button ID (e.g., BTN_SOUTH)
                    # event.value = 1 (Pressed), 0 (Released)
                    self.dispatcher.process_button(event.code, event.value)
                    
                elif event.type == ecodes.EV_ABS:
                    # Handle analog movement and pressure features
                    self.process_analog_axis(event.code, event.value)
        finally:
            device.ungrab()

    def process_analog_axis(self, axis_code, raw_value):
        # F310 typical axis limits: -32768 to 32767
        self.axis_states[axis_code] = raw_value
        
        # Calculate deviation based on the profile's specific Threshold
        profile_threshold = self.dispatcher.get_current_threshold()
        
        # Normalized pressure scale for proportional velocity adjustments
        if abs(raw_value) > profile_threshold:
            max_range = 32768 - profile_threshold
            direction = 1 if raw_value > 0 else -1
            pressure_ratio = (abs(raw_value) - profile_threshold) / max_range
            
            # Forward pressure calculations directly to the virtual output pipeline
            self.dispatcher.process_axis_movement(axis_code, direction, pressure_ratio)
        else:
            # Inside deadzone
            self.dispatcher.process_axis_movement(axis_code, 0, 0.0)
