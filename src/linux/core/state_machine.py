# src/core/state_machine.py
class ActionDispatcher:
    def __init__(self, parsed_profiles, default_profile="Main"):
        self.profiles = parsed_profiles
        self.current_profile_name = default_profile
        self.active_profile = self.profiles.get(default_profile, {"threshold": 4000, "buttons": {}, "axes": {}})
        self.base_profile_name = default_profile
        
        # Track physical states to prevent stuck triggers during runtime profile shifts
        self.pressed_buttons = set()
        self.output_driver = None  # Will be bound dynamically by the active platform handler

    def bind_output_driver(self, driver):
        self.output_driver = driver

    def get_current_threshold(self):
        return self.active_profile.get("threshold", 4000)

    def process_button(self, btn_id, is_pressed):
        """Processes chorded macros and dynamic system profiling layers."""
        mapping = self.active_profile["buttons"].get(btn_id)
        
        if is_pressed:
            self.pressed_buttons.add(btn_id)
            if not mapping or not self.output_driver:
                return
                
            if mapping["type"] == "KEYBOARD":
                # Execute combo/macro sequences synchronously 
                for key_code in mapping["keys"]:
                    self.output_driver.press_key(key_code)
                    
            elif mapping["type"] == "PROFILE_SHIFT":
                # Layer Switching: Swaps map layers on active hold
                target = mapping["target"]
                if target in self.profiles:
                    self.current_profile_name = target
                    self.active_profile = self.profiles[target]
                    
        else:
            if btn_id in self.pressed_buttons:
                self.pressed_buttons.remove(btn_id)
                
            if not mapping or not self.output_driver:
                return
                
            if mapping["type"] == "KEYBOARD":
                for key_code in mapping["keys"]:
                    self.output_driver.release_key(key_code)
                    
            elif mapping["type"] == "PROFILE_SHIFT":
                # Revert layer safely when button chord state ends
                self.current_profile_name = self.base_profile_name
                self.active_profile = self.profiles[self.base_profile_name]
                # Clear all active keystrokes to eliminate sticking modifiers across shifts
                self.output_driver.release_all()

    def process_axis_movement(self, axis_name, direction, pressure_ratio):
        """Proportional navigation handler for mouse speed scaling profiles."""
        # axis_name combined with direction creates JoyToKey mapping keys like 'axis1n' or 'axis1p'
        suffix = 'n' if direction < 0 else 'p'
        lookup_key = f"{axis_name}{suffix}".lower()
        
        mapping = self.active_profile["axes"].get(lookup_key)
        if not mapping or not self.output_driver:
            return
            
        if mapping["type"] == "MOUSE" and direction != 0:
            # Dynamic pressure scaling calculus (Input pressure weights the relative shift speed)
            target_x = int(mapping["x"] * pressure_ratio)
            target_y = int(mapping["y"] * pressure_ratio)
            target_wheel = mapping["wheel"] # Wheel jumps do not scale continuously
            
            if target_x != 0 or target_y != 0:
                self.output_driver.move_mouse(target_x, target_y)
            if target_wheel != 0:
                self.output_driver.scroll_mouse(target_wheel)
                
        elif mapping["type"] == "KEYBOARD":
            # Handles analog stick thresholds triggering simple keystrokes (e.g., analog stick to WASD)
            if direction != 0:
                for key_code in mapping["keys"]:
                    self.output_driver.press_key(key_code)
            else:
                # Release fallback when centering stick axis inside threshold zones
                for suffix_check in ['n', 'p']:
                    fallback_map = self.active_profile["axes"].get(f"{axis_name}{suffix_check}".lower())
                    if fallback_map and fallback_map["type"] == "KEYBOARD":
                        for key_code in fallback_map["keys"]:
                            self.output_driver.release_key(key_code)
