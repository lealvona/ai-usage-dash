# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect pkg_resources and its dependencies
datas_pkg_resources, binaries_pkg_resources, hiddenimports_pkg_resources = collect_all('pkg_resources')

# Also collect jaraco modules that pkg_resources needs
try:
    from PyInstaller.utils.hooks import collect_data_files
    jaraco_datas = collect_data_files('jaraco.text')
except:
    jaraco_datas = []

block_cipher = None

# Application metadata
app_name = 'AI Usage Dashboard'
app_version = '1.0.0'
app_description = 'Track and visualize AI usage across multiple providers'

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=binaries_pkg_resources,
    datas=datas_pkg_resources + [
        ('gui_templates', 'gui_templates'),
        ('gui_static', 'gui_static'),
    ],
    hiddenimports=hiddenimports_pkg_resources + [
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
        # Explicitly include jaraco modules
        'jaraco',
        'jaraco.text',
        'jaraco.context',
        'jaraco.functools',
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
