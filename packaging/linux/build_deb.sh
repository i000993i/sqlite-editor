#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

VERSION="${1:-1.0.0}"
PKG_ROOT="pkg"

if [ ! -d "dist/SQLiteViewer" ]; then
    echo "Ошибка: dist/SQLiteViewer не найден. Сначала запустите build.py"
    exit 1
fi

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/DEBIAN"
mkdir -p "$PKG_ROOT/opt/sqlite-viewer"
mkdir -p "$PKG_ROOT/usr/bin"
mkdir -p "$PKG_ROOT/usr/share/applications"
mkdir -p "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps"

cp -r dist/SQLiteViewer/* "$PKG_ROOT/opt/sqlite-viewer/"
ln -sf /opt/sqlite-viewer/SQLiteViewer "$PKG_ROOT/usr/bin/sqlite-viewer"

if [ -f icons/app.png ]; then
    cp icons/app.png "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps/sqlite-viewer.png"
fi

cp packaging/linux/sqlite-viewer.desktop "$PKG_ROOT/usr/share/applications/"

cat > "$PKG_ROOT/DEBIAN/control" <<EOF
Package: sqlite-viewer
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: SQLite Viewer <noreply@example.com>
Description: SQLite Table Viewer
 Cross-platform SQLite database viewer/editor with dark theme,
 SQL editor, charts and import/export.
Depends: libgl1, libegl1, libxkbcommon0, libxcb-cursor0, libfuse2
EOF

chmod -R 755 "$PKG_ROOT/opt/sqlite-viewer"
chmod 644 "$PKG_ROOT/usr/share/applications/sqlite-viewer.desktop"

dpkg-deb --build --root-owner-group "$PKG_ROOT" \
    "sqlite-viewer_${VERSION}_amd64.deb"

echo "✅ Готово: sqlite-viewer_${VERSION}_amd64.deb"