"""Streamlit UI for PDF link highlighting."""

import logging
from typing import List, Tuple

import streamlit as st

try:
    import fitz  # PyMuPDF
except ImportError:
    st.error("PyMuPDF is not installed. Please run: uv add pymupdf")
    st.stop()

from core import (
    detect_links, highlight_links, parse_color_string,
    get_link_statistics
)


# Configure logging for Streamlit
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def setup_page():
    """Setup Streamlit page configuration."""
    st.set_page_config(
        page_title="PDFリンクハイライター",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("📄 PDFリンクハイライター")
    st.markdown("PDFファイル内のリンク領域を自動的にハイライトします")


def sidebar_controls():
    """Render sidebar controls and return configuration."""
    st.sidebar.header("設定")

    # File upload
    uploaded_files = st.sidebar.file_uploader(
        "PDFファイルをアップロード",
        type=['pdf'],
        accept_multiple_files=True,
        help="処理するPDFファイルを1つまたは複数選択してください"
    )

    st.sidebar.divider()

    # Color configuration
    st.sidebar.subheader("ハイライト設定")

    # Color picker with text input fallback
    color_mode = st.sidebar.radio(
        "色の入力方法",
        ["カラーピッカー", "テキスト入力"],
        help="ハイライト色の指定方法を選択してください"
    )

    if color_mode == "カラーピッカー":
        color_hex = st.sidebar.color_picker(
            "ハイライト色",
            value="#FFFF00",
            help="ハイライト色を選択してください"
        )
        color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    else:
        color_text = st.sidebar.text_input(
            "色（hex または r,g,b）",
            value="#FFFF00",
            help="#RRGGBB または r,g,b（0-1の範囲）で色を入力してください"
        )
        try:
            color_rgb = parse_color_string(color_text)
        except ValueError as e:
            st.sidebar.error(f"無効な色の形式: {e}")
            color_rgb = (1.0, 1.0, 0.0)  # Default to yellow

    # Opacity slider
    opacity = st.sidebar.slider(
        "透明度",
        min_value=0.1,
        max_value=0.9,
        value=0.35,
        step=0.05,
        help="ハイライトの透明度（低い値ほど透明になります）"
    )

    # Mode selection
    mode = st.sidebar.selectbox(
        "ハイライトモード",
        ["draw", "annot"],
        index=0,
        help="互換性を重視する場合は'draw'がおすすめです"
    )

    # Minimum side filter
    min_side = st.sidebar.number_input(
        "最小サイズ（pt）",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5,
        help="この値より小さいリンクを除外します"
    )

    st.sidebar.divider()

    # Password input
    password = st.sidebar.text_input(
        "PDFパスワード",
        type="password",
        help="暗号化されたPDFのパスワードを入力してください（必要な場合）"
    )

    # Process button
    process_button = st.sidebar.button(
        "🎯 リンクをハイライト",
        type="primary",
        disabled=not uploaded_files,
        help="アップロードしたPDFファイルを処理します"
    )

    return {
        'uploaded_files': uploaded_files,
        'color_rgb': color_rgb,
        'opacity': opacity,
        'mode': mode,
        'min_side': min_side,
        'password': password if password else None,
        'process_button': process_button
    }


def process_pdf_file(
    file_data: bytes,
    filename: str,
    config: dict
) -> Tuple[bytes, dict, str]:
    """Process a single PDF file.

    Returns:
        Tuple of (processed_pdf_bytes, statistics, log_messages)
    """
    log_messages = []

    def capture_log(msg: str, level: str = "INFO"):
        log_messages.append(f"{level}: {msg}")
        if level == "ERROR":
            logger.error(msg)
        else:
            logger.info(msg)

    try:
        # Open document from bytes
        doc = fitz.open(stream=file_data, filetype="pdf")

        # Handle password if needed
        if doc.needs_pass:
            if not config['password']:
                raise RuntimeError("PDF is encrypted but no password provided")

            if not doc.authenticate(config['password']):
                raise RuntimeError("Incorrect password for encrypted PDF")

        capture_log(f"Opened PDF: {filename} ({len(doc)} pages)")

        # Detect links
        capture_log("リンクを検出中...")
        annots = detect_links(doc)

        if not annots:
            capture_log("PDFにリンクが見つかりませんでした", "WARNING")
            stats = {"total_links": 0, "by_kind": {}, "by_page": {}}
        else:
            # Get statistics
            stats = get_link_statistics(annots)
            capture_log(f"Detected {len(annots)} links: {dict(stats['by_kind'])}")

            # Highlight links
            capture_log("リンクをハイライト中...")
            highlight_links(
                doc,
                annots,
                color=config['color_rgb'],
                opacity=config['opacity'],
                mode=config['mode'],
                min_side=config['min_side']
            )

            # Count filtered links
            filtered_count = len([a for a in annots if a.passes_min_side_filter(config['min_side'])])
            capture_log(f"Highlighted {filtered_count} links")

        # Save to bytes
        pdf_bytes = doc.write()
        doc.close()

        capture_log("処理が正常に完了しました")
        return pdf_bytes, stats, "\n".join(log_messages)

    except Exception as e:
        capture_log(f"Error processing {filename}: {str(e)}", "ERROR")
        if 'doc' in locals():
            doc.close()
        raise


def display_statistics(stats_list: List[dict], filenames: List[str]):
    """Display processing statistics."""
    if not stats_list:
        return

    st.subheader("📊 処理結果")

    # Summary metrics
    total_files = len(stats_list)
    total_links = sum(stats.get("total_links", 0) for stats in stats_list)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("処理済みファイル", total_files)
    with col2:
        st.metric("検出されたリンク数", total_links)
    with col3:
        avg_links = total_links / total_files if total_files > 0 else 0
        st.metric("1ファイルあたりの平均リンク数", f"{avg_links:.1f}")

    # Detailed results
    if total_files > 1:
        st.subheader("ファイル別の結果")
        for i, (filename, stats) in enumerate(zip(filenames, stats_list)):
            with st.expander(f"📄 {filename}", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**リンクの種類:**")
                    for link_type, count in stats.get("by_kind", {}).items():
                        st.write(f"- {link_type}: {count}")

                with col2:
                    st.write("**リンクのあるページ:**")
                    page_stats = stats.get("by_page", {})
                    if page_stats:
                        for page, count in sorted(page_stats.items(), key=lambda x: int(x[0])):
                            st.write(f"- {int(page) + 1}ページ: {count}")
                    else:
                        st.write("- リンクが見つかりませんでした")


def display_preview(pdf_bytes: bytes, filename: str):
    """Display PDF preview (first page).

    Note: This is a basic implementation. For full preview with highlights,
    you would need pdf2image and additional image processing.
    """
    try:
        st.subheader(f"📄 プレビュー: {filename}")
        st.info("プレビューは最初のページを表示します。ハイライトはこのプレビューでは表示されない場合があります。")

        # For now, just show basic document info
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        st.write(f"**ページ数:** {len(doc)}")
        st.write(f"**サイズ:** {len(pdf_bytes):,} バイト")

        # You could add pdf2image-based preview here:
        # if pdf2image is available:
        #     from pdf2image import convert_from_bytes
        #     images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        #     if images:
        #         st.image(images[0], width=600)

        doc.close()

    except Exception as e:
        st.error(f"プレビューを生成できませんでした: {e}")


def main():
    """Main Streamlit app."""
    setup_page()

    # Sidebar controls
    config = sidebar_controls()

    # Main content area
    if not config['uploaded_files']:
        st.info("👆 サイドバーを使用してPDFファイルをアップロードしてください。")
        st.markdown("""
        ## 使用方法

        1. **PDFアップロード**: サイドバーのファイルアップローダーを使用
        2. **設定**: ハイライト色、透明度、その他のオプションを設定
        3. **処理**: 「リンクをハイライト」をクリックしてファイルを処理
        4. **ダウンロード**: ハイライト済みPDFをダウンロードボタンで取得

        ## 機能

        - **複数ファイル**: 複数のPDFを一度に処理
        - **カスタマイズ可能なハイライト**: 色と透明度を選択
        - **スマートフィルタリング**: 小さなリンクを自動的に除外
        - **バッチ処理**: 複数ファイルを効率的に処理
        - **パスワード対応**: 暗号化されたPDFにも対応
        """)
        return

    # Show uploaded files info
    st.subheader(f"📁 アップロードされたファイル ({len(config['uploaded_files'])})")
    for file in config['uploaded_files']:
        file_size = len(file.read())
        file.seek(0)  # Reset file pointer
        st.write(f"- **{file.name}** ({file_size:,} バイト)")

    # Processing
    if config['process_button']:
        process_files(config)


def process_files(config: dict):
    """Process uploaded files."""
    files = config['uploaded_files']

    # Initialize session state for results
    if 'processing_results' not in st.session_state:
        st.session_state.processing_results = {}

    st.subheader("🔄 ファイルを処理中")

    progress_bar = st.progress(0)
    status_text = st.empty()

    processed_files = []
    statistics_list = []
    failed_files = []

    for file_idx, uploaded_file in enumerate(files):
        filename = uploaded_file.name
        progress = (file_idx + 1) / len(files)

        status_text.text(f"処理中: {filename}")
        progress_bar.progress(progress)

        try:
            # Read file data
            file_data = uploaded_file.read()
            uploaded_file.seek(0)  # Reset for potential reuse

            # Process PDF
            with st.status(f"{filename}を処理中...", expanded=True):
                st.write("🔍 リンクを検出中...")

                processed_bytes, stats, log_msg = process_pdf_file(
                    file_data, filename, config
                )

                st.write("✅ 処理が完了しました")
                st.code(log_msg, language="text")

            # Store results
            processed_files.append((filename, processed_bytes))
            statistics_list.append(stats)

            # Cache in session state
            st.session_state.processing_results[filename] = {
                'data': processed_bytes,
                'stats': stats,
                'log': log_msg
            }

        except Exception as e:
            st.error(f"❌ {filename}の処理に失敗しました: {str(e)}")
            failed_files.append((filename, str(e)))

    progress_bar.progress(1.0)
    status_text.text(f"{len(files)}個のファイルの処理が完了しました")

    # Show results
    if processed_files:
        st.success(f"✅ {len(processed_files)}個のファイルを正常に処理しました")

        # Display statistics
        display_statistics(statistics_list, [f[0] for f in processed_files])

        # Download buttons
        st.subheader("📥 結果をダウンロード")

        for filename, pdf_bytes in processed_files:
            output_filename = filename.replace('.pdf', '_hl.pdf')

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{output_filename}**")
            with col2:
                st.download_button(
                    label="ダウンロード",
                    data=pdf_bytes,
                    file_name=output_filename,
                    mime="application/pdf",
                    key=f"download_{filename}"
                )

    if failed_files:
        st.error(f"❌ {len(failed_files)}個のファイルの処理に失敗しました")
        with st.expander("エラーを表示", expanded=False):
            for filename, error in failed_files:
                st.write(f"**{filename}**: {error}")


if __name__ == "__main__":
    main()