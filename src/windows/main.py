# /src/windows/main.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import JoyToKeyConfigParser
from device_listener import WindowsGamepadEngine
from virtual_output import WindowsVirtualOutputDriver

def main():
    print("====================================================")
    print(" ControlToKey - Windows Subsystem Engine Launching  ")
    print("====================================================")
    
    profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
    if not os.path.exists(profiles_dir):
        os.makedirs(profiles_dir)
        print(f"[*] Created profiles folder at: {profiles_dir}")

    parser = JoyToKeyConfigParser(profiles_dir)
    parser.load_all_profiles()
    
    if not parser.loaded_profiles:
        print("[!] Warning: No configurations found. Injecting a default profile slot.")
        parser.loaded_profiles["Main"] = {"threshold": 4000, "buttons": {}, "axes": {}}

    default_profile = "Main" if "Main" in parser.loaded_profiles else list(parser.loaded_profiles.keys())[0]
    print(f"[*] Loaded Windows Profiles: {list(parser.loaded_profiles.keys())}")

    try:
        output_driver = WindowsVirtualOutputDriver()
        engine = WindowsGamepadEngine(default_profile_name=default_profile, parsed_profiles=parser.loaded_profiles)
        engine.bind_output_driver(output_driver)
        
        engine.start_loop()
    except KeyboardInterrupt:
        print("\n[*] ControlToKey safely shutting down.")

if __name__ == "__main__":
    main()
