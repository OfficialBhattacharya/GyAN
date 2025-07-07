# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('frameworkArchitecture.txt', '.')],
    hiddenimports=['PyQt5.sip', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'email.mime.text', 'email.mime.multipart', 'email.utils', 'smtplib', 'apscheduler', 'apscheduler.schedulers', 'apscheduler.schedulers.background', 'apscheduler.executors', 'apscheduler.executors.pool', 'apscheduler.job', 'apscheduler.triggers', 'apscheduler.triggers.cron', 'apscheduler.util', 'bs4', 'beautifulsoup4', 'requests', 'urllib3', 'lxml', 'lxml.etree', 'lxml._elementpath', 'json', 'logging', 'datetime', 'copy', 're', 'os', 'sys'],
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
    name='UPSC-News-Aggregator',
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
