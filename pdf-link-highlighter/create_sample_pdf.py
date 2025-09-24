#!/usr/bin/env python3
"""Create a sample PDF with various types of links for testing."""

import fitz  # PyMuPDF
from pathlib import Path


def create_sample_pdf(output_path: str = "examples/sample.pdf"):
    """Create a sample PDF with different types of links."""

    # Create a new PDF document
    doc = fitz.open()

    # Page 1: External links and email
    page1 = doc.new_page(width=595, height=842)  # A4 size

    # Add some text and links
    page1.insert_text((50, 100), "PDF Link Highlighter - Sample Document",
                     fontsize=18, color=(0, 0, 0))

    page1.insert_text((50, 150), "This document contains various types of links for testing:",
                     fontsize=12, color=(0, 0, 0))

    # External URL link
    page1.insert_text((50, 200), "• External website: https://www.example.com",
                     fontsize=12, color=(0, 0, 1))
    link_annot = page1.add_link_annot(fitz.Rect(180, 185, 350, 205))
    link_annot.set_uri("https://www.example.com")
    link_annot.update()

    # Email link
    page1.insert_text((50, 230), "• Email contact: contact@example.com",
                     fontsize=12, color=(0, 0, 1))
    page1.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(160, 215, 320, 235),
        "uri": "mailto:contact@example.com"
    })

    # Secure website
    page1.insert_text((50, 260), "• Secure site: https://secure.example.org/login",
                     fontsize=12, color=(0, 0, 1))
    page1.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(150, 245, 400, 265),
        "uri": "https://secure.example.org/login"
    })

    # Internal page link
    page1.insert_text((50, 290), "• Go to page 2 (internal link)",
                     fontsize=12, color=(0, 0, 1))
    page1.add_link({
        "kind": fitz.LINK_GOTO,
        "from": fitz.Rect(50, 275, 250, 295),
        "page": 1  # 0-based, so page 2
    })

    # Phone number link
    page1.insert_text((50, 320), "• Call us: +1-555-123-4567",
                     fontsize=12, color=(0, 0, 1))
    page1.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(110, 305, 260, 325),
        "uri": "tel:+1-555-123-4567"
    })

    # Small link (should be filtered out by min-side filter)
    page1.insert_text((50, 350), "• Tiny link: X",
                     fontsize=12, color=(0, 0, 1))
    page1.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(160, 348, 162, 350),  # 2x2 pixel link
        "uri": "https://tiny.example.com"
    })

    # Large clickable area
    page1.insert_text((50, 400), "Large clickable area (rectangle below):",
                     fontsize=12, color=(0, 0, 0))
    page1.draw_rect(fitz.Rect(50, 420, 300, 480), color=(0.8, 0.8, 0.8), width=1)
    page1.insert_text((60, 450), "Click anywhere in this gray box to visit our homepage",
                     fontsize=10, color=(0, 0, 0))
    page1.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(50, 420, 300, 480),
        "uri": "https://www.homepage.example.com"
    })

    # Page 2: More internal navigation
    page2 = doc.new_page(width=595, height=842)

    page2.insert_text((50, 100), "Page 2 - Internal Navigation",
                     fontsize=18, color=(0, 0, 0))

    page2.insert_text((50, 150), "You reached this page via an internal link!",
                     fontsize=12, color=(0, 0, 0))

    # Back to page 1
    page2.insert_text((50, 200), "• Back to page 1",
                     fontsize=12, color=(0, 0, 1))
    page2.add_link({
        "kind": fitz.LINK_GOTO,
        "from": fitz.Rect(50, 185, 180, 205),
        "page": 0  # Back to page 1
    })

    # FTP link
    page2.insert_text((50, 230), "• FTP server: ftp://files.example.com/downloads/",
                     fontsize=12, color=(0, 0, 1))
    page2.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(130, 215, 420, 235),
        "uri": "ftp://files.example.com/downloads/"
    })

    # Documentation links
    page2.insert_text((50, 260), "• Documentation: https://docs.example.com/api/v1",
                     fontsize=12, color=(0, 0, 1))
    page2.add_link({
        "kind": fitz.LINK_URI,
        "from": fitz.Rect(170, 245, 420, 265),
        "uri": "https://docs.example.com/api/v1"
    })

    # Multiple links in a table-like format
    page2.insert_text((50, 320), "Quick Links:", fontsize=14, color=(0, 0, 0))

    links_data = [
        ("Home", "https://www.example.com", 350),
        ("About", "https://www.example.com/about", 370),
        ("Contact", "https://www.example.com/contact", 390),
        ("Support", "mailto:support@example.com", 410)
    ]

    for text, url, y_pos in links_data:
        page2.insert_text((70, y_pos), f"• {text}", fontsize=12, color=(0, 0, 1))
        page2.add_link({
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(70, y_pos - 5, 70 + len(text) * 8, y_pos + 10),
            "uri": url
        })

    # Save the document
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc.save(str(output_path))
    doc.close()

    print(f"Sample PDF created: {output_path}")
    print(f"PDF contains {sum(len(page.get_links()) for page in doc if hasattr(page, 'get_links'))} links")

    return output_path


if __name__ == "__main__":
    create_sample_pdf()