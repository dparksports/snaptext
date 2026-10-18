# -*- mode: python ; coding: utf-8 -*-
"""Build contract for standalone snaptext binaries.

One command, every OS (run natively on each platform - PyInstaller does not
cross-compile):

    pip install -e ".[build]"
    pyinstaller snaptext.spec

Produces dist/snaptext/ (onedir: faster startup, far fewer antivirus false
positives than onefile) with the OCR models bundled, so first run works
offline. This same spec is what release CI runs, so DIY builds and official
builds cannot drift apart.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("rapidocr_onnxruntime", include_py_files=False)
binaries = collect_dynamic_libs("onnxruntime")

hiddenimports = [
    "rapidocr_onnxruntime",
    # loaded at runtime via importlib from config.yaml - invisible to static
    # analysis, so they must be declared explicitly:
    "rapidocr_onnxruntime.ch_ppocr_v3_det",
    "rapidocr_onnxruntime.ch_ppocr_v3_rec",
    "rapidocr_onnxruntime.ch_ppocr_v2_cls",
    "onnxruntime",
    "pymupdf",
    "pypdf",
    "pyperclip",
    "mss",
    "keyboard",
]

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="snaptext",
    debug=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="snaptext",
)
