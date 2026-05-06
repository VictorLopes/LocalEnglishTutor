# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('config.json', '.'), ('profile.jpg', '.'), ('images', 'images'), ('assets', 'assets')]
binaries = []
hiddenimports = ['PySide6.QtSvg']

# Collect all dependencies for AI models
deps = [
    'onnxruntime', 'faster_whisper', 'kokoro_onnx', 
    'espeakng_loader', 'phonemizer', 'language_tags', 
    'segments', 'csvw'
]

for dep in deps:
    tmp_ret = collect_all(dep)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

a = Analysis(
    ['src/app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='LocalEnglishTutor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
    icon=['icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LocalEnglishTutor',
)
app = BUNDLE(
    coll,
    name='LocalEnglishTutor.app',
    icon='icon.icns',
    bundle_identifier='com.localenglishtutor.app',
    info_plist={
        'NSMicrophoneUsageDescription': 'This app needs access to your microphone to transcribe your speech for the AI English Tutor.',
        'LSMinimumSystemVersion': '10.13',
    },
)
