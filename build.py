"""
Единый скрипт сборки для Windows 10/11 и Linux (Zorin/Ubuntu/Debian).
Использование:
    python build.py             # GUI
    python build.py --console   # с консолью (отладка)
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd):
    print("→", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, cwd=ROOT)


def ensure_icons():
    """Если icons/app.png или app.ico отсутствуют — создаём заглушки."""
    icons = ROOT / "icons"
    icons.mkdir(exist_ok=True)

    png = icons / "app.png"
    ico = icons / "app.ico"

    if png.exists() and ico.exists():
        return

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt

        app = QApplication.instance() or QApplication([])

        pix = QPixmap(256, 256)
        pix.fill(QColor("#1a1a1a"))

        painter = QPainter(pix)
        painter.setPen(QColor("#ff4444"))
        font = QFont("Sans", 96, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "DB")
        painter.end()

        if not png.exists():
            pix.save(str(png))
            print(f"→ создана иконка {png}")

        if not ico.exists() and sys.platform.startswith("win"):
            pix.save(str(ico))
            print(f"→ создана иконка {ico}")
    except Exception as e:
        print(f"⚠ Не удалось сгенерировать иконки: {e}")


def main():
    console = "--console" in sys.argv

    ensure_icons()

    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)

    spec = "SQLiteViewer.spec"
    extra = ["--console"] if console else []
    run([sys.executable, "-m", "PyInstaller", spec, "--noconfirm", *extra])

    src_icons = ROOT / "icons"
    dst_icons = ROOT / "dist" / "SQLiteViewer" / "icons"
    if src_icons.exists() and not dst_icons.exists():
        shutil.copytree(src_icons, dst_icons)

    exe_name = ("SQLiteViewer.exe" if sys.platform.startswith("win")
                else "SQLiteViewer")
    print("\n✅ Готово:", ROOT / "dist" / "SQLiteViewer" / exe_name)


if __name__ == "__main__":
    main()