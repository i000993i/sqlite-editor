import sys
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def run(cmd):
    print("→", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    console = "--console" in sys.argv

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