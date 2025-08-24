# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for XML Watcher Service

import sys
import os
from pathlib import Path

# Get the absolute path to the project root (current working directory)
ROOT_DIR = Path(os.getcwd())

a = Analysis(
    ['src/main.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        # Include the example config file
        ('config/config.yaml.example', 'config'),
    ],
    hiddenimports=[
        'watchdog.observers',
        'colorlog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='xml-watcher',
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
    # Add version info for Windows
    version='version_info.py' if sys.platform == 'win32' else None,
    # Set icon if available
    icon=None,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='XML-Watcher.app',
        icon=None,
        bundle_identifier='com.xmlwatcher.service',
        info_plist={
            'CFBundleName': 'XML Watcher',
            'CFBundleDisplayName': 'XML Watcher Service',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
        },
    )
