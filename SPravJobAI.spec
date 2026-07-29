# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('scraper_service', 'scraper_service'),
        ('knowledge_base', 'knowledge_base'),
        ('templates', 'templates'),
        ('app_icon_v2.ico', '.')
    ] + collect_data_files('playwright') + collect_data_files('playwright_stealth'),
    hiddenimports=[
        'engine',
        'engine.daemon',
        'engine.utils',
        'api',
        'uvicorn',
        'fastapi',
        'webview',
        'sqlite3',
        'chromadb.telemetry.product.posthog',
        'chromadb.api.rust',
        'langgraph',
        'langgraph.pregel',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'playwright.sync_api'
    ] + collect_submodules('engine') + collect_submodules('discovery'),
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
    [],
    exclude_binaries=True,
    name='SPravJobAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app_icon_v2.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SPravJobAI',
)
