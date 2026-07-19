# src/linux/core/config_parser.py
import configparser
import os

class JoyToKeyConfigParser:
    def __init__(self, profiles_dir):
        self.profiles_dir = profiles_dir
        self.loaded_profiles = {}

    def load_all_profiles(self):
        """Pre-loads all .cfg profiles into memory to allow instantaneous layer switching."""
        if not os.path.exists(self.profiles_dir):
            return
        for file in os.listdir(self.profiles_dir):
            if file.endswith('.cfg'):
                path = os.path.join(self.profiles_dir, file)
                profile_name = os.path.splitext(file)[0]
                self.loaded_profiles[profile_name] = self.parse_file(path)

    def parse_file(self, file_path):
        config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        config.read(file_path)
        
        profile_data = {
            "threshold": 4000, # Default JoyToKey deadzone threshold (out of 32768)
            "buttons": {},
            "axes": {}
        }
        
        # 1. Parse global deadzone threshold
        if 'General' in config:
            # JoyToKey uses an integer threshold (e.g., 1000 to 20000)
            if 'Threshold' in config['General']:
                profile_data["threshold"] = config.getint('General', 'Threshold')
        
        # 2. Parse active control mappings
        target_section = 'Joystick 1' if 'Joystick 1' in config else config.sections()[0] if config.sections() else None
        
        if target_section and target_section in config:
            for key, value in config[target_section].items():
                clean_val = value.strip()
                if not clean_val:
                    continue
                
                # JoyToKey encodes mappings as comma-separated values: KeyType, Param1, Param2, ...
                raw_params = [v.strip() for v in clean_val.split(',')]
                
                # Handle standard button assignments (Button01, Button02, etc.)
                if key.startswith('button'):
                    try:
                        btn_index = int(key.replace('button', ''))
                        profile_data["buttons"][btn_index] = self._parse_mapping_type(raw_params)
                    except ValueError:
                        continue
                        
                # Handle directional stick/POV assignments (Axis1n, Axis1p, Slider1n, etc.)
                elif key.startswith('axis') or key.startswith('slider') or key.startswith('pov'):
                    profile_data["axes"][key.lower()] = self._parse_mapping_type(raw_params)
                    
        return profile_data

    def _parse_mapping_type(self, params):
        """
        Translates JoyToKey code strings into actionable execution blocks.
        JoyToKey standard types:
        - Type 1: Direct Keyboard Mapping (Values are Windows Virtual Key ints)
        - Type 2: Mouse Cursor/Wheel Emulation
        - Type 3: Special functions (e.g., Profile Swapping / Layering)
        """
        if not params:
            return None
            
        try:
            mapping_type = int(params[0])
        except ValueError:
            return {"type": "UNKNOWN", "raw": params}

        if mapping_type == 1:
            # Direct Key or Macro Chain (Sequential entries represent chorded execution combos)
            keys = []
            for p in params[1:]:
                if p and p != '0':
                    try:
                        keys.append(int(p))
                    except ValueError:
                        pass
            return {"type": "KEYBOARD", "keys": keys}
            
        elif mapping_type == 2:
            # Mouse motion or scrolling vector
            # Params: 2, MouseX_Speed, MouseY_Speed, Wheel_Direction
            try:
                return {
                    "type": "MOUSE",
                    "x": int(params[1]) if len(params) > 1 else 0,
                    "y": int(params[2]) if len(params) > 2 else 0,
                    "wheel": int(params[3]) if len(params) > 3 else 0
                }
            except ValueError:
                return {"type": "MOUSE", "x": 0, "y": 0, "wheel": 0}
                
        elif mapping_type == 3:
            # Profile / Layer Switching Shift Features
            # Param[1] usually holds the configuration filename target string or target index
            target_profile = params[1] if len(params) > 1 else ""
            return {"type": "PROFILE_SHIFT", "target": target_profile.replace('"', '')}
            
        return {"type": "UNKNOWN", "raw": params}
