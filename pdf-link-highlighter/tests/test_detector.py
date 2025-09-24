"""Tests for link detection functionality."""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.detector import detect_links, filter_by_min_side, get_link_statistics, _determine_link_kind
from core.annot_model import LinkAnnot


class TestLinkDetection:
    """Test link detection functionality."""

    def test_determine_link_kind_uri(self):
        """Test link kind determination for URI links."""
        link = {"uri": "https://example.com"}
        assert _determine_link_kind(link) == "uri"

    def test_determine_link_kind_page(self):
        """Test link kind determination for page links."""
        link = {"page": 5}
        assert _determine_link_kind(link) == "page"

    def test_determine_link_kind_named(self):
        """Test link kind determination for named links."""
        link = {"named": "bookmark1"}
        assert _determine_link_kind(link) == "named"

    def test_determine_link_kind_file(self):
        """Test link kind determination for file links."""
        link = {"file": "document.pdf"}
        assert _determine_link_kind(link) == "file"

    def test_determine_link_kind_unknown(self):
        """Test link kind determination for unknown links."""
        link = {}
        assert _determine_link_kind(link) == "unknown"

    def test_filter_by_min_side(self):
        """Test minimum side filtering."""
        annots = [
            LinkAnnot(0, (0, 0, 5, 5), "uri", {}),      # 5x5, passes
            LinkAnnot(0, (0, 0, 1, 10), "uri", {}),     # 1x10, fails (min side = 1)
            LinkAnnot(0, (0, 0, 3, 4), "uri", {}),      # 3x4, passes
        ]

        filtered = filter_by_min_side(annots, 2.0)

        assert len(filtered) == 2
        assert filtered[0].rect == (0, 0, 5, 5)
        assert filtered[1].rect == (0, 0, 3, 4)

    def test_get_link_statistics(self):
        """Test link statistics generation."""
        annots = [
            LinkAnnot(0, (0, 0, 5, 5), "uri", {}),
            LinkAnnot(1, (0, 0, 3, 4), "uri", {}),
            LinkAnnot(1, (0, 0, 2, 2), "page", {}),
        ]

        stats = get_link_statistics(annots)

        assert stats["total_links"] == 3
        assert stats["by_kind"]["uri"] == 2
        assert stats["by_kind"]["page"] == 1
        assert stats["by_page"]["0"] == 1
        assert stats["by_page"]["1"] == 2

    @patch('core.detector.fitz')
    def test_detect_links_success(self, mock_fitz):
        """Test successful link detection."""
        # Mock document and page
        mock_doc = Mock()
        mock_page = Mock()

        # Mock document length
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page

        # Mock page properties
        mock_page.rotation = 0
        mock_page.get_links.return_value = [
            {"from": (0, 0, 100, 20), "uri": "https://example.com"},
            {"from": (0, 25, 50, 45), "page": 2}
        ]

        # Call function
        result = detect_links(mock_doc)

        # Verify results
        assert len(result) == 2
        assert result[0].page_index == 0
        assert result[0].rect == (0, 0, 100, 20)
        assert result[0].kind == "uri"
        assert result[1].kind == "page"

    @patch('core.detector.fitz')
    def test_detect_links_no_links(self, mock_fitz):
        """Test link detection with no links."""
        mock_doc = Mock()
        mock_page = Mock()

        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_page.rotation = 0
        mock_page.get_links.return_value = []

        result = detect_links(mock_doc)

        assert len(result) == 0


class TestLinkAnnotModel:
    """Test LinkAnnot data model."""

    def test_link_annot_properties(self):
        """Test LinkAnnot property calculations."""
        annot = LinkAnnot(0, (10, 20, 50, 80), "uri", {})

        assert annot.width == 40
        assert annot.height == 60
        assert annot.min_side == 40

    def test_passes_min_side_filter(self):
        """Test minimum side filter method."""
        annot1 = LinkAnnot(0, (0, 0, 5, 10), "uri", {})  # min_side = 5
        annot2 = LinkAnnot(0, (0, 0, 1, 10), "uri", {})  # min_side = 1

        assert annot1.passes_min_side_filter(3.0) == True
        assert annot1.passes_min_side_filter(5.0) == True
        assert annot1.passes_min_side_filter(6.0) == False

        assert annot2.passes_min_side_filter(0.5) == True
        assert annot2.passes_min_side_filter(1.0) == True
        assert annot2.passes_min_side_filter(2.0) == False