#!/bin/bash
#
# Build TeamViewer ID Changer thành .app cho macOS
# Chạy: bash build-app.sh
#

APP_NAME="TeamViewer ID Changer"
SCRIPT="TeamViewer-ID-Changer-GUI.py"
APP_DIR="${APP_NAME}.app"
CONTENTS="${APP_DIR}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"

echo "🔨 Đang tạo ${APP_DIR}..."

# Xoá app cũ nếu có
rm -rf "${APP_DIR}"

# Tạo cấu trúc .app
mkdir -p "${MACOS}"
mkdir -p "${RESOURCES}"

# Copy script chính
cp "${SCRIPT}" "${MACOS}/app.py"

# Copy icon nếu có
if [ -f "AppIcon.icns" ]; then
    cp "AppIcon.icns" "${RESOURCES}/AppIcon.icns"
    echo "  ✓ Icon added"
fi

# Tạo launcher script
cat > "${MACOS}/launcher" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON=$(which python3 2>/dev/null || echo "/usr/bin/python3")
exec "${PYTHON}" "${DIR}/app.py"
LAUNCHER

chmod +x "${MACOS}/launcher"

# Tạo Info.plist
cat > "${CONTENTS}/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.local.teamviewer-id-changer</string>
    <key>CFBundleVersion</key>
    <string>7.0</string>
    <key>CFBundleShortVersionString</key>
    <string>7.0</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
PLIST

echo "✅ Đã tạo xong: ${APP_DIR}"
echo ""
echo "Cách dùng:"
echo "  1. Double-click '${APP_DIR}' để chạy"
echo "  2. macOS sẽ hỏi mật khẩu Admin khi cần"
echo ""
echo "Nếu macOS chặn (Gatekeeper): chuột phải > Open > Open"
