# -*- mode: python ; coding: utf-8 -*-
# Console version for debugging

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icons', 'icons')],
    hiddenimports=[
        'pandas', 'openpyxl', 'reportlab', 'reportlab.pdfbase', 'reportlab.pdfbase.ttfonts',
        'matplotlib', 'matplotlib.backends.backend_qtagg',
        'functions', 'functions.logger', 'functions.database', 'functions.import_export',
        'functions.styles', 'functions.utils', 'functions.table_designer',
        'functions.table_viewer_virtual', 'functions.virtual_table_model',
        'functions.async_manager', 'functions.sql_editor', 'functions.data_visualizer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SQLiteViewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icons\\app_icon.ico'],
)
