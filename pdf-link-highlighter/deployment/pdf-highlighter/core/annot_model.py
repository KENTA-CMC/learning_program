"""Core data models for PDF link annotation."""

from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class LinkAnnot:
    """Represents a link annotation found in a PDF page.

    Attributes:
        page_index: Page number (0-based)
        rect: Rectangle coordinates (x0, y0, x1, y1) in page coordinates
        kind: Link type ("uri", "page", "named", "file", "unknown")
        raw: Original dictionary from PyMuPDF get_links()
    """
    page_index: int
    rect: Tuple[float, float, float, float]  # x0, y0, x1, y1
    kind: str  # "uri" | "page" | "named" | "file" | "unknown"
    raw: Dict[str, Any]  # get_links() の元辞書

    @property
    def width(self) -> float:
        """Rectangle width."""
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> float:
        """Rectangle height."""
        return self.rect[3] - self.rect[1]

    @property
    def min_side(self) -> float:
        """Minimum side length (width or height)."""
        return min(self.width, self.height)

    def passes_min_side_filter(self, min_side_threshold: float) -> bool:
        """Check if this annotation passes the minimum side filter."""
        return self.min_side >= min_side_threshold