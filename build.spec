# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Application metadata
app_name = 'AI Usage Dashboard'
app_version = '1.0.0'
app_description = 'Track and visualize AI usage across multiple providers'

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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon here
)

# For Windows, also create a console version for debugging
exe_console = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ai_usage_dash_console',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console version for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
