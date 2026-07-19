# main.py
import sys
import os
from src.core.config_parser import JoyToKeyConfigParser
from src.core.state_machine import ActionDispatcher

def main():
    print("Initializing ControlToKey Core Subsystems...")
    
    # Establish local profiles path targeting the medical profile structures
    profiles_dir = os.path.join(os.path.dirname(__file__), "profiles")
    
    parser = JoyToKeyConfigParser(profiles_dir)
    parser.load_all_profiles()
    
    if not parser.loaded_profiles:
        print(f"Warning: No valid .cfg profiles resolved in folder: {profiles_dir}")
        # Inject an empty runtime container fallback structure
        parser.loaded_profiles["Main"] = {"threshold": 4000, "buttons": {}, "axes": {}}

    # Fall back safely to alphabetical primary if a 'Main.cfg' file wasn't directly found
    default_node = "Main" if "Main" in parser.loaded_profiles else list(parser.loaded_profiles.keys())[0]
    
    dispatcher = ActionDispatcher(parser.loaded_profiles, default_profile=default_node)

    # Resolve platform framework engine execution hooks dynamically
    if sys.platform.startswith('linux'):
        print("Linux OS confirmed. Running uinput platform device execution wrappers...")
        from src.linux.virtual_output import LinuxVirtualOutputDriver
        from src.linux.device_listener import LinuxGamepadEngine
        
        output_driver = LinuxVirtualOutputDriver()
        dispatcher.bind_output_driver(output_driver)
        
        # Note: LinuxGamepadEngine uses dispatcher under the hood to process direct loop streams
        # Ensure the device path target rules match your udev assignments safely!
        try:
            from src.linux.device_listener import LinuxGamepadEngine
            engine = LinuxGamepadEngine()
            engine.dispatcher = dispatcher
            engine.start_loop()
        except Exception as err:
            print(f"Kernel initialization exception raised: {err}")
            print("Ensure execution context has read-write access permissions to uinput and event interfaces.")
    else:
        print(f"Architecture platform hook target '{sys.platform}' is currently unmapped.")

if __name__ == "__main__":
    main()
