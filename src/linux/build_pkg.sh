#!/usr/bin/env bash
# /build_pkg.sh

PKG_DIR="controltokey_1.0-1_amd64"
rm -rf "$PKG_DIR"

# 1. Structure the canonical Debian deployment files
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/controltokey"
mkdir -p "$PKG_DIR/lib/systemd/system"

# 2. Write the Package Metadata Manifest
cat << EOF > "$PKG_DIR/DEBIAN/control"
Package: controltokey
Version: 1.0-1
Section: utils
Priority: optional
Architecture: amd64
Maintainer: VirusTC
Depends: python3, python3-pip, python3-evdev
Description: Core translation engine for JoyToKey profile parsing on Linux hardware.
EOF

# 3. Inject Post-Installation Configuration Setup Execution script
cat << EOF > "$PKG_DIR/DEBIAN/postinst"
#!/bin/sh
chmod +x /opt/controltokey/main.py
systemctl daemon-reload
systemctl enable controltokey.service
systemctl start controltokey.service
exit 0
EOF
chmod 555 "$PKG_DIR/DEBIAN/postinst"

# ====================================================================
# NEW: Inject Pre-Removal Cleanups Setup Configuration Script
# ====================================================================
cp src/linux/prerm "$PKG_DIR/DEBIAN/prerm"
chmod 555 "$PKG_DIR/DEBIAN/prerm"

# 4. Move runtime configurations and system rules safely into package paths
cp -r src/linux/* "$PKG_DIR/opt/controltokey/"
cp "$PKG_DIR/opt/controltokey/controltokey.service" "$PKG_DIR/lib/systemd/system/"

# Create udev rules directly inside package structure
mkdir -p "$PKG_DIR/etc/udev/rules.d"
cat << EOF > "$PKG_DIR/etc/udev/rules.d/99-controltokey.rules"
KERNEL=="uinput", MODE="0660", GROUP="input"
KERNEL=="event*", ATTRS{idVendor}=="046d", ATTRS{idProduct}=="c216", MODE="0660", GROUP="input"
EOF

# 5. Compile into an installable hospital distribution archive
dpkg-deb --build "$PKG_DIR"
echo "[*] Compiled standalone architecture distribution: ${PKG_DIR}.deb"
