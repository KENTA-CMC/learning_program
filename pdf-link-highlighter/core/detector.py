"""Link detection functionality for PDF files."""

import logging
from typing import List

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: uv add pymupdf")

from .annot_model import LinkAnnot

logger = logging.getLogger(__name__)


def detect_links(doc: fitz.Document) -> List[LinkAnnot]:
    """Detect all link annotations in a PDF document.

    Uses PyMuPDF's page.get_links() to collect all link rectangles from all pages.

    Args:
        doc: PyMuPDF Document object

    Returns:
        List of LinkAnnot objects representing all detected links

    Example:
        >>> import fitz
        >>> doc = fitz.open("sample.pdf")
        >>> links = detect_links(doc)
        >>> print(f"Found {len(links)} links")
    """
    annots = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Log page rotation for debugging coordinate issues
        if page.rotation != 0:
            logger.debug(f"Page {page_num} has rotation: {page.rotation}°")

        try:
            links = page.get_links()
            logger.debug(f"Page {page_num}: found {len(links)} links")

            for link in links:
                # Determine link kind based on available fields
                kind = _determine_link_kind(link)

                # Extract rectangle coordinates
                rect = link.get("from")
                if rect is None:
                    logger.warning(f"Page {page_num}: link missing 'from' rectangle, skipping")
                    continue

                # Convert fitz.Rect to tuple if needed
                if hasattr(rect, 'x0'):
                    rect_tuple = (rect.x0, rect.y0, rect.x1, rect.y1)
                else:
                    rect_tuple = tuple(rect)

                annot = LinkAnnot(
                    page_index=page_num,
                    rect=rect_tuple,
                    kind=kind,
                    raw=link
                )

                annots.append(annot)

        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}")
            continue

    logger.info(f"Total links detected: {len(annots)}")
    return annots


def _determine_link_kind(link: dict) -> str:
    """Determine the kind of link based on available fields.

    Args:
        link: Dictionary from page.get_links()

    Returns:
        Link kind string: "uri", "page", "named", "file", or "unknown"
    """
    if link.get("uri"):
        return "uri"
    elif link.get("page") is not None:
        return "page"
    elif link.get("named"):
        return "named"
    elif link.get("file"):
        return "file"
    else:
        return "unknown"


def filter_by_min_side(annots: List[LinkAnnot], min_side: float) -> List[LinkAnnot]:
    """Filter annotations by minimum side length.

    This helps exclude tiny advertisement links or other unwanted small rectangles.

    Args:
        annots: List of LinkAnnot objects
        min_side: Minimum side length in points (default should be 2.0)

    Returns:
        Filtered list of LinkAnnot objects
    """
    filtered = [a for a in annots if a.passes_min_side_filter(min_side)]

    removed_count = len(annots) - len(filtered)
    if removed_count > 0:
        logger.info(f"Filtered out {removed_count} links smaller than {min_side}pt")

    return filtered


def get_link_statistics(annots: List[LinkAnnot]) -> dict:
    """Get statistics about detected links.

    Args:
        annots: List of LinkAnnot objects

    Returns:
        Dictionary with link statistics by kind and page
    """
    stats = {
        "total_links": len(annots),
        "by_kind": {},
        "by_page": {},
    }

    for annot in annots:
        # Count by kind
        stats["by_kind"][annot.kind] = stats["by_kind"].get(annot.kind, 0) + 1

        # Count by page
        page_key = str(annot.page_index)
        stats["by_page"][page_key] = stats["by_page"].get(page_key, 0) + 1

    return stats