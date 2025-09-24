#!/usr/bin/env python3
"""Create a simple sample PDF for testing (without programmatic links)."""

import fitz  # PyMuPDF
from pathlib import Path


def create_simple_sample(output_path: str = "examples/sample.pdf"):
    """Create a simple PDF document with text content."""

    # Create a new PDF document
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page(width=595, height=842)  # A4 size

    # Add content
    page1.insert_text((50, 100), "PDF Link Highlighter - Test Document",
                     fontsize=18, color=(0, 0, 0))

    page1.insert_text((50, 150), "This is a simple test document.",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((50, 180), "To test the link highlighter, use a PDF that already contains",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((50, 200), "clickable links, such as:",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((70, 230), "• Academic papers with citation links",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((70, 250), "• Business documents with URLs",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((70, 270), "• Forms with email or website links",
                     fontsize=12, color=(0, 0, 0))

    page1.insert_text((70, 290), "• Documents with internal page references",
                     fontsize=12, color=(0, 0, 0))

    # Page 2
    page2 = doc.new_page(width=595, height=842)

    page2.insert_text((50, 100), "Page 2 - Usage Instructions",
                     fontsize=16, color=(0, 0, 0))

    instructions = [
        "1. Command Line Usage:",
        "   python highlight_links.py --input your-document.pdf",
        "",
        "2. Web Interface:",
        "   streamlit run app_streamlit.py",
        "",
        "3. Batch Processing:",
        "   python highlight_links.py --batch ./pdf-folder/",
        "",
        "4. Custom Colors:",
        "   python highlight_links.py --input doc.pdf --color \"#FF0000\"",
        "",
        "The application will automatically detect and highlight",
        "any clickable links in your PDF documents."
    ]

    y_pos = 140
    for line in instructions:
        page2.insert_text((50, y_pos), line, fontsize=10, color=(0, 0, 0))
        y_pos += 20

    # Save the document
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc.save(str(output_path))
    doc.close()

    print(f"Simple sample PDF created: {output_path}")
    return output_path


if __name__ == "__main__":
    create_simple_sample()