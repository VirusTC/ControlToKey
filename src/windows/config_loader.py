# /src/windows/config_loader.py
import configparser
import os

class JoyToKeyConfigParser:
    def __init__(self, profiles_dir):
        self.profiles_dir = profiles_dir
        self.loaded_profiles = {}

    def load_all_profiles(self):
        """Pre-loads all profiles to ensure near-zero latency when changing layers."""
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
            "threshold": 4000,  # JoyToKey's default deadzone axis baseline
            "buttons": {},
            "axes": {}
        }
        
        if 'General' in config and 'Threshold' in config['General']:
            try:
                profile_data["threshold"] = config.getint('General', 'Threshold')
            except ValueError:
                pass
        
        section = 'Joystick 1' if 'Joystick 1' in config else (config.sections()[0] if config.sections() else None)
        
        if section and section in config:
            for key, value in config[section].items():
                clean_val = value.strip()
                if not clean_val:
                    continue
                
                raw_params = [v.strip() for v in clean_val.split(',')]
                
                if key.startswith('button'):
                    try:
                        btn_index = int(key.replace('button', ''))
                        profile_data["buttons"][btn_index] = self._parse_mapping_type(raw_params)
                    except ValueError:
                        continue
                elif key.startswith('axis') or key.startswith('slider') or key.startswith('pov'):
                    profile_data["axes"][key.lower()] = self._parse_mapping_type(raw_params)
                    
        return profile_data

    def _parse_mapping_type(self, params):
        if not params:
            return None
            
        try:
            mapping_type = int(params[0])
        except ValueError:
            return {"type": "UNKNOWN", "raw": params}

        if mapping_type == 1:
            # Keyboard Type: Collects sequential macro execution chains
            keys = []
            for p in params[1:]:
                if p and p != '0':
                    try:
                        keys.append(int(p))
                    except ValueError:
                        pass
            return {"type": "KEYBOARD", "keys": keys}
            
        elif mapping_type == 2:
            # Mouse Type: Relative cursor translation & scrolling steps
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
            # Layer Shift Type: Changes profiles dynamically on click-hold
            target_profile = params[1] if len(params) > 1 else ""
            return {"type": "PROFILE_SHIFT", "target": target_profile.replace('"', '')}
            
        return {"type": "UNKNOWN", "raw": params}
