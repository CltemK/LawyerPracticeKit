# -*- mode: python ; coding: utf-8 -*-
import os

datas = [
    ('使用说明.txt', '.'),
    ('必看-首次使用说明.txt', '.'),
]

hiddenimports = [
    'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
    'docx', 'docx.oxml', 'docx.oxml.ns', 'docx.shared', 'docx.enum.text',
    'PIL', 'PIL.Image',
    'requests', 'urllib3', 'charset_normalizer', 'idna', 'certifi',
    'cryptography', 'cryptography.fernet',
    'cryptography.hazmat.backends.openssl',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'paddle', 'paddleocr', 'paddlepaddle',
        'easyocr', 'torch', 'torchvision',
        'skimage', 'scipy', 'matplotlib', 'pandas',
        'numpy', 'cv2', 'shapely', 'pyclipper',
        'tests', 'pytest', 'unittest', 'tkinter',
    ],
    noarchive=False,
    optimize=1,
)

# 过滤掉配置文件，避免打包密钥
a.datas = [x for x in a.datas if not x[0].startswith('config')]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='微信截图整理工具',
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
    icon='resources/icon.ico' if os.path.exists('resources/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='微信截图整理工具',
)
