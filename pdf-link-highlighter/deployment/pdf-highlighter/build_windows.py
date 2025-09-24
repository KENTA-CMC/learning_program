#!/usr/bin/env python3
"""
Windows用実行ファイル生成スクリプト
このスクリプトをWindows環境で実行してください。
"""

import subprocess
import sys
import os

def install_requirements():
    """必要なパッケージをインストール"""
    requirements = [
        'pyinstaller',
        'pymupdf>=1.23.0',
        'streamlit>=1.28.0',
        'pdf2image>=1.16.0'
    ]

    for req in requirements:
        print(f"Installing {req}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])

def build_exe():
    """Windows用exeファイルをビルド"""
    print("Building Windows executable...")

    # PyInstallerでビルド
    cmd = [
        'pyinstaller',
        'app_streamlit.spec',
        '--noconfirm'
    ]

    subprocess.check_call(cmd)
    print("Build completed! Check the 'dist' folder for PDF_Link_Highlighter.exe")

if __name__ == '__main__':
    print("PDF Link Highlighter - Windows Builder")
    print("=====================================")

    # Windowsかチェック
    if os.name != 'nt':
        print("Warning: This script should be run on Windows for Windows executable generation.")
        print("Current OS detected:", os.name)
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

    try:
        install_requirements()
        build_exe()
        print("\nSuccess! Windows executable created.")
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        sys.exit(1)