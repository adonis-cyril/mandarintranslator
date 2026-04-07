#!/bin/bash
# Creates a Zhumu.app bundle that can be double-clicked to launch the app.
# Run this once after setup.sh to create the app in /Applications.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Zhumu"
APP_DIR="/Applications/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

echo "=== Creating ${APP_NAME}.app ==="

# Create app bundle structure
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Create the launcher script
cat > "${MACOS_DIR}/${APP_NAME}" << LAUNCHER
#!/bin/bash
# Zhumu launcher — runs the app with the project virtualenv
cd "${SCRIPT_DIR}"
exec "${SCRIPT_DIR}/.venv/bin/python" main.py
LAUNCHER
chmod +x "${MACOS_DIR}/${APP_NAME}"

# Create Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Zhumu</string>
    <key>CFBundleDisplayName</key>
    <string>Zhumu (驻目)</string>
    <key>CFBundleIdentifier</key>
    <string>com.zhumu.transcriber</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleExecutable</key>
    <string>Zhumu</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

echo ""
echo "=========================================="
echo "  ${APP_NAME}.app created in /Applications!"
echo "=========================================="
echo ""
echo "  You can now:"
echo "  - Open it from /Applications"
echo "  - Drag it to your Dock for quick access"
echo "  - Search 'Zhumu' in Spotlight (Cmd+Space)"
echo ""
