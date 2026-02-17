# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui_templates', 'gui_templates'),
        ('gui_static', 'gui_static'),
    ],
    hiddenimports=[
        'flask',
        'webview',
        'cryptography',
        'requests',
        'psutil',
        'PIL',
        'matplotlib',
        'colorlog',
        'encryption_manager',
        'enhanced_providers',
        'enhanced_api_client',
        # Core modules
        'pkg_resources',
        'importlib',
        'importlib.metadata',
    ],
    hooksconfig={
        'pkg_resources': {
            'excludes': ['jaraco']
        }
    },
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'tests',
        'test',
        # Exclude unnecessary packages
        'tkinter',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai_usage_dash',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
