# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

project_root = Path(SPECPATH)
is_windows = sys.platform.startswith("win")

icon_path = project_root / "icons" / ("app.ico" if is_windows else "app.png")
icon = str(icon_path) if icon_path.exists() else None

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(project_root / "icons"), "icons")],
    hiddenimports=[
        "pandas", "numpy", "openpyxl", "reportlab", "matplotlib",
        "matplotlib.backends.backend_qtagg",
        "PyQt6.QtCore", "PyQt6.QtGui", "PyQt6.QtWidgets", "PyQt6.QtSvg",
        "sqlite3", "pandas._libs.tslibs.timedeltas",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="SQLiteViewer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=is_windows,
    console=False,
    disable_windowed_traceback=False,
    icon=icon,
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False, upx=is_windows, upx_exclude=[],
    name="SQLiteViewer",
)