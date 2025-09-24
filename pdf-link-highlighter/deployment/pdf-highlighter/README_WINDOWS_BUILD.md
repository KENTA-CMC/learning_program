# Windows実行ファイル生成手順

## 前提条件
- Windows 10/11
- Python 3.8以上

## 手順

### 1. ファイルの準備
以下のファイルをWindowsマシンにコピーしてください：
```
pdf-highlighter/
├── app_streamlit.py
├── app_streamlit.spec
├── build_windows.py
├── core/
│   ├── __init__.py
│   ├── annot_model.py
│   ├── detector.py
│   ├── painter.py
│   └── io_utils.py
└── requirements.txt
```

### 2. 自動ビルド（推奨）
コマンドプロンプトまたはPowerShellで実行：
```cmd
python build_windows.py
```

### 3. 手動ビルド
```cmd
# 依存関係をインストール
pip install pyinstaller pymupdf streamlit pdf2image

# exeファイルを生成
pyinstaller app_streamlit.spec --noconfirm
```

### 4. 結果
`dist/PDF_Link_Highlighter.exe` が生成されます。

## 実行方法
```cmd
# コマンドプロンプトから実行
PDF_Link_Highlighter.exe

# または、ダブルクリックで実行
```

実行すると：
1. コンソールウィンドウが開く
2. Streamlitサーバーが起動
3. ブラウザが自動で開く（開かない場合は http://localhost:8501 にアクセス）

## 注意事項
- 初回起動時は少し時間がかかります
- ウイルス対策ソフトが警告する場合があります（誤検出）
- ファイルサイズは約150-200MBになります（全依存関係を含むため）

## トラブルシューティング

### "DLL load failed" エラー
Microsoft Visual C++ Redistributable をインストール：
https://aka.ms/vs/17/release/vc_redist.x64.exe

### "No module named" エラー
requirements.txtの依存関係が不足している可能性があります：
```cmd
pip install -r requirements.txt
```

### ブラウザが開かない
手動で以下のURLにアクセス：
http://localhost:8501