# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the directory containing the spec file
block_cipher = None
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all necessary data files and hidden imports
datas = []
hiddenimports = []

# Streamlit data files
streamlit_datas = collect_data_files('streamlit')
datas.extend(streamlit_datas)

# Streamlit hidden imports
streamlit_imports = collect_submodules('streamlit')
hiddenimports.extend(streamlit_imports)

# Add specific streamlit components
hiddenimports.extend([
    'streamlit.web.cli',
    'streamlit.web.bootstrap',
    'streamlit.runtime.scriptrunner.script_runner',
    'streamlit.runtime.state',
    'streamlit.elements',
    'streamlit.components.v1',
    'streamlit.components.v1.html',
    'streamlit.components.v1.iframe',
    'streamlit.components.v1.declare_component',
    'altair',
    'plotly',
    'plotly.graph_objects',
    'plotly.express',
    'plotly.offline',
    'pyarrow',
    'pyarrow.csv',
    'pyarrow.json',
    'pyarrow.parquet',
    'pandas',
    'numpy',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'pdf2image',
    'pdf2image.pdf2image',
    'fitz',  # PyMuPDF
    'pymupdf',
])

# Core module data
core_datas = []
core_path = os.path.join(current_dir, 'core')
if os.path.exists(core_path):
    for root, dirs, files in os.walk(core_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, current_dir)
                core_datas.append((file_path, os.path.dirname(rel_path)))

datas.extend(core_datas)

a = Analysis(
    ['app_streamlit.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'qtpy',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    name='PDF_Link_Highlighter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True for console app to see Streamlit output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have an icon file
)