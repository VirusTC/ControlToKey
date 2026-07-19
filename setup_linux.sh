#!/usr/bin/env bash
# /setup_linux.sh

echo "===================================================="
echo " Preparing ControlToKey Local Linux Workstation Tool"
echo "===================================================="

# 1. Inject the Udev device rules so non-root users can write inputs
echo "[*] Configuration setup: Registering hardware udev accessibility rules..."
sudo bash -c 'cat << EOF > /etc/udev/rules.rules.d/99-controltokey.rules
# Allow non-privileged execution processing for F310 Gamepad inputs and Virtual Output streams
KERNEL=="uinput", MODE="0660", GROUP="input"
KERNEL=="event*", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="c216", MODE="0660", GROUP="input"
EOF'

# 2. Trigger the OS subsystem rules to update immediately
sudo udevadm control --reload-rules && sudo udevadm trigger

# 3. Add current operational user profile to the input pipeline pool
echo "[*] Registering active system profile into input processing pool..."
sudo usermod -aG input $USER

# 4. Install standard framework dependencies
echo "[*] Finalizing system library dependencies..."
pip install python-evdev python-uinput

echo ""
echo "===================================================="
echo " Setup complete! Please log out and back in for the "
echo " permissions group update to take effect.           "
echo " Execute using: python src/linux/main.py             "
echo "===================================================="
