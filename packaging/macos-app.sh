#!/usr/bin/env bash
# Wrap the PyInstaller output in a macOS .app bundle.
# Run after `pyinstaller snaptext.spec` produced dist/snaptext/
#
#   bash packaging/macos-app.sh
#
# Unsigned: the first launch needs right-click > Open (or System Settings >
# Privacy & Security > "Open Anyway"). Notarization requires an Apple
# Developer ID ($99/yr) and is intentionally out of scope for DIY builds.
set -euo pipefail

APP="Snaptext.app"
VERSION="$(python3 -c 'import snaptext; print(snaptext.__version__)')"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp -R dist/snaptext/. "$APP/Contents/MacOS/"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key> <string>snaptext</string>
  <key>CFBundleIdentifier</key> <string>io.github.dparksports.snaptext</string>
  <key>CFBundleName</key> <string>Snaptext</string>
  <key>CFBundlePackageType</key> <string>APPL</string>
  <key>CFBundleShortVersionString</key> <string>${VERSION}</string>
</dict>
</plist>
EOF

echo "built $APP (v${VERSION}) - unsigned; first launch: right-click > Open"
