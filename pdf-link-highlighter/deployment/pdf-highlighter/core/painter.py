"""Highlight painting functionality for PDF link annotations."""

import logging
from typing import List, Tuple, Literal

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: uv add pymupdf")

from .annot_model import LinkAnnot

logger = logging.getLogger(__name__)


def highlight_links(
    doc: fitz.Document,
    annots: List[LinkAnnot],
    *,
    color: Tuple[float, float, float] = (1, 1, 0),  # Yellow
    opacity: float = 0.35,
    mode: Literal['draw', 'annot'] = 'draw',
    min_side: float = 2.0
) -> None:
    """Highlight link annotations in a PDF document.

    Modifies the document directly. Use save_doc() to write to file.

    Args:
        doc: PyMuPDF Document object to modify
        annots: List of LinkAnnot objects to highlight
        color: RGB color tuple (0-1 range), default yellow (1,1,0)
        opacity: Fill opacity (0-1 range), default 0.35
        mode: 'draw' for direct rectangle drawing (recommended), 'annot' for annotation
        min_side: Minimum side length filter in points, default 2.0

    Example:
        >>> import fitz
        >>> from core.detector import detect_links
        >>> doc = fitz.open("sample.pdf")
        >>> links = detect_links(doc)
        >>> highlight_links(doc, links, color=(1, 1, 0), opacity=0.35)
        >>> doc.save("highlighted.pdf")
    """
    # Filter by minimum side first
    filtered_annots = [a for a in annots if a.passes_min_side_filter(min_side)]

    removed_count = len(annots) - len(filtered_annots)
    if removed_count > 0:
        logger.info(f"Filtering {removed_count} links smaller than {min_side}pt")

    if not filtered_annots:
        logger.warning("No links to highlight after filtering")
        return

    # Validate color and opacity
    color = _validate_color(color)
    opacity = _validate_opacity(opacity)

    # Group annotations by page for efficient processing
    page_groups = {}
    for annot in filtered_annots:
        if annot.page_index not in page_groups:
            page_groups[annot.page_index] = []
        page_groups[annot.page_index].append(annot)

    total_highlighted = 0

    for page_index, page_annots in page_groups.items():
        if page_index >= len(doc):
            logger.warning(f"Page index {page_index} out of range, skipping")
            continue

        page = doc[page_index]

        for annot in page_annots:
            try:
                if mode == 'draw':
                    _draw_highlight_rect(page, annot, color, opacity)
                elif mode == 'annot':
                    _add_highlight_annotation(page, annot, color, opacity)
                else:
                    raise ValueError(f"Invalid mode: {mode}")

                total_highlighted += 1

            except Exception as e:
                logger.error(f"Failed to highlight link on page {page_index}: {e}")
                continue

        logger.debug(f"Page {page_index}: highlighted {len(page_annots)} links")

    logger.info(f"Successfully highlighted {total_highlighted} links")


def _draw_highlight_rect(
    page: fitz.Page,
    annot: LinkAnnot,
    color: Tuple[float, float, float],
    opacity: float
) -> None:
    """Draw a filled rectangle highlight using page.draw_rect().

    This is the recommended approach as it's more robust and doesn't depend
    on viewer annotation support.
    """
    rect = fitz.Rect(annot.rect)

    # Draw filled rectangle with no border (width=0)
    page.draw_rect(
        rect,
        fill=color,
        fill_opacity=opacity,
        width=0  # No border
    )


def _add_highlight_annotation(
    page: fitz.Page,
    annot: LinkAnnot,
    color: Tuple[float, float, float],
    opacity: float
) -> None:
    """Add a highlight annotation using page.add_rect_annot().

    This approach creates actual PDF annotations but may render differently
    across viewers.
    """
    rect = fitz.Rect(annot.rect)

    # Create rectangle annotation
    highlight_annot = page.add_rect_annot(rect)

    # Set colors and opacity
    highlight_annot.set_colors({'fill': color})
    highlight_annot.set_opacity(opacity)

    # Update the annotation
    highlight_annot.update()


def _validate_color(color: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Validate and clamp color values to 0-1 range."""
    if len(color) != 3:
        raise ValueError("Color must be a tuple of 3 values (R, G, B)")

    return tuple(max(0.0, min(1.0, float(c))) for c in color)


def _validate_opacity(opacity: float) -> float:
    """Validate and clamp opacity value to 0-1 range."""
    return max(0.0, min(1.0, float(opacity)))


def parse_color_string(color_str: str) -> Tuple[float, float, float]:
    """Parse color string to RGB tuple.

    Supports formats:
    - "#RRGGBB" (hex)
    - "r,g,b" (comma-separated floats 0-1)

    Args:
        color_str: Color string to parse

    Returns:
        RGB tuple (0-1 range)

    Raises:
        ValueError: If color string format is invalid
    """
    color_str = color_str.strip()

    # Hex format: #RRGGBB
    if color_str.startswith('#'):
        if len(color_str) != 7:
            raise ValueError("Hex color must be in format #RRGGBB")

        try:
            r = int(color_str[1:3], 16) / 255.0
            g = int(color_str[3:5], 16) / 255.0
            b = int(color_str[5:7], 16) / 255.0
            return (r, g, b)
        except ValueError:
            raise ValueError("Invalid hex color format")

    # Comma-separated format: "r,g,b"
    elif ',' in color_str:
        try:
            parts = [float(x.strip()) for x in color_str.split(',')]
            if len(parts) != 3:
                raise ValueError("Color must have exactly 3 components")
            return tuple(parts)
        except ValueError:
            raise ValueError("Invalid comma-separated color format")

    else:
        raise ValueError("Color must be in format #RRGGBB or r,g,b")