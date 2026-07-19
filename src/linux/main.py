# /src/linux/main.py
import os
import sys

# Ensure local imports work cleanly if run from the repository root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import JoyToKeyConfigParser
from device_listener import LinuxGamepadEngine
from virtual_output import LinuxVirtualOutputDriver

def main():
    print("====================================================")
    print(" ControlToKey - Linux Subsystem Engine Launching   ")
    print("====================================================")
    
    # Target profiles directory relative to this folder
    # Expected structure: /src/linux/profiles/*.cfg
    profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
    if not os.path.exists(profiles_dir):
        os.makedirs(profiles_dir)
        print(f"[*] Created empty profiles folder at: {profiles_dir}")
        print("[!] Please place your JoyToKey hospital profiles (.cfg) inside it.")

    # 1. Parse JoyToKey .cfg configs
    parser = JoyToKeyConfigParser(profiles_dir)
    parser.load_all_profiles()
    
    if not parser.loaded_profiles:
        print("[!] Warning: No configurations detected. Injecting a default profile slot.")
        parser.loaded_profiles["Main"] = {"threshold": 4000, "buttons": {}, "axes": {}}

    # Determine default startup baseline mapping profile 
    default_profile = "Main" if "Main" in parser.loaded_profiles else list(parser.loaded_profiles.keys())[0]
    print(f"[*] Loaded profiles: {list(parser.loaded_profiles.keys())}")
    print(f"[*] Core active profile layer: [{default_profile}]")

    # 2. Spin up Hardware Listeners & Output Pipelines
    try:
        output_driver = LinuxVirtualOutputDriver()
        engine = LinuxGamepadEngine(default_profile_name=default_profile, parsed_profiles=parser.loaded_profiles)
        engine.bind_output_driver(output_driver)
        
        print("[*] Core components bound. Starting input tracking loop...")
        engine.start_loop()
        
    except PermissionError:
        print("\n[X] Error: Insufficient permissions to access uinput or joystick events!")
        print("[*] Solution: Ensure your user belongs to the 'input' group or run with sudo.")
    except FileNotFoundError as fnf:
        print(f"\n[X] Hardware Error: {fnf}")
    except KeyboardInterrupt:
        print("\n[*] ControlToKey safely shutting down.")

if __name__ == "__main__":
    main()
