import configparser

def parse_joytokey_cfg(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    profile = {
        "threshold": config.getint('General', 'Threshold', fallback=0),
        "buttons": {},
        "axes": {}
    }

    # Parse [Joystick 1] section
    if 'Joystick 1' in config:
        for key, value in config['Joystick 1'].items():
            # Handle Button Mappings (e.g., Button01=65)
            if key.startswith('button'):
                btn_id = int(key.replace('button', ''))
                # JoyToKey can list multiple keys for one button (Combinations/Macros)
                keys = [int(k) for k in value.split(',')] 
                profile["buttons"][btn_id] = keys
            
            # Handle Axis Mappings (Pressure/Direction)
            # Format: Axis<ID><Direction> = <Type>, <Param1>, <Param2>
            # Example: Axis1n=2, -50, 0, 0 (Mouse Move Left, Speed 50)
            elif key.startswith('axis'):
                # Logic to parse axis string into action
                profile["axes"][key] = [int(v) for v in value.split(',')]
                
    return profile
