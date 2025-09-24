"""Tests for highlight painting functionality."""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.painter import (
    highlight_links, parse_color_string, _validate_color, _validate_opacity,
    _draw_highlight_rect, _add_highlight_annotation
)
from core.annot_model import LinkAnnot


class TestColorParsing:
    """Test color parsing functionality."""

    def test_parse_hex_color(self):
        """Test hex color parsing."""
        result = parse_color_string("#FF0000")
        assert result == (1.0, 0.0, 0.0)

        result = parse_color_string("#00FF00")
        assert result == (0.0, 1.0, 0.0)

        result = parse_color_string("#0000FF")
        assert result == (0.0, 0.0, 1.0)

        result = parse_color_string("#FFFF00")
        assert result == (1.0, 1.0, 0.0)

    def test_parse_comma_separated_color(self):
        """Test comma-separated color parsing."""
        result = parse_color_string("1.0,0.0,0.0")
        assert result == (1.0, 0.0, 0.0)

        result = parse_color_string("0.5, 0.7, 0.9")
        assert result == (0.5, 0.7, 0.9)

        result = parse_color_string("1,1,0")
        assert result == (1.0, 1.0, 0.0)

    def test_parse_color_invalid_format(self):
        """Test invalid color format handling."""
        with pytest.raises(ValueError, match="Color must be in format"):
            parse_color_string("invalid")

        with pytest.raises(ValueError, match="Invalid hex color format"):
            parse_color_string("#GG0000")

        with pytest.raises(ValueError, match="Color must have exactly 3 components"):
            parse_color_string("1,2")

        with pytest.raises(ValueError, match="Invalid comma-separated color format"):
            parse_color_string("a,b,c")

    def test_validate_color(self):
        """Test color validation and clamping."""
        # Valid colors
        assert _validate_color((1.0, 0.5, 0.0)) == (1.0, 0.5, 0.0)

        # Clamping
        assert _validate_color((-0.1, 1.5, 0.5)) == (0.0, 1.0, 0.5)

        # Invalid length
        with pytest.raises(ValueError, match="Color must be a tuple of 3 values"):
            _validate_color((1.0, 0.5))

    def test_validate_opacity(self):
        """Test opacity validation and clamping."""
        assert _validate_opacity(0.5) == 0.5
        assert _validate_opacity(-0.1) == 0.0
        assert _validate_opacity(1.5) == 1.0


class TestHighlighting:
    """Test highlighting functionality."""

    @patch('core.painter.fitz')
    def test_draw_highlight_rect(self, mock_fitz):
        """Test rectangle drawing."""
        mock_page = Mock()
        mock_rect_class = Mock()
        mock_fitz.Rect = mock_rect_class

        annot = LinkAnnot(0, (10, 20, 50, 60), "uri", {})

        _draw_highlight_rect(mock_page, annot, (1, 1, 0), 0.35)

        # Verify Rect was created with correct coordinates
        mock_rect_class.assert_called_once_with((10, 20, 50, 60))

        # Verify draw_rect was called with correct parameters
        mock_page.draw_rect.assert_called_once()
        call_args = mock_page.draw_rect.call_args

        assert call_args[1]['fill'] == (1, 1, 0)
        assert call_args[1]['fill_opacity'] == 0.35
        assert call_args[1]['width'] == 0

    @patch('core.painter.fitz')
    def test_add_highlight_annotation(self, mock_fitz):
        """Test annotation addition."""
        mock_page = Mock()
        mock_annot = Mock()
        mock_rect_class = Mock()

        mock_fitz.Rect = mock_rect_class
        mock_page.add_rect_annot.return_value = mock_annot

        annot = LinkAnnot(0, (10, 20, 50, 60), "uri", {})

        _add_highlight_annotation(mock_page, annot, (0, 1, 0), 0.5)

        # Verify annotation creation
        mock_page.add_rect_annot.assert_called_once()
        mock_annot.set_colors.assert_called_once_with({'fill': (0, 1, 0)})
        mock_annot.set_opacity.assert_called_once_with(0.5)
        mock_annot.update.assert_called_once()

    @patch('core.painter.fitz')
    def test_highlight_links_filtering(self, mock_fitz):
        """Test link filtering in highlight_links."""
        mock_doc = Mock()

        # Create test annotations - some below min_side threshold
        annots = [
            LinkAnnot(0, (0, 0, 10, 10), "uri", {}),     # 10x10, passes
            LinkAnnot(0, (0, 0, 1, 1), "uri", {}),       # 1x1, fails
            LinkAnnot(0, (0, 0, 5, 5), "uri", {}),       # 5x5, passes
        ]

        # Mock document length and page
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        mock_doc.__getitem__.return_value = mock_page

        # Mock fitz.Rect
        mock_fitz.Rect = Mock()

        # Call highlight_links with min_side=2.0
        highlight_links(mock_doc, annots, min_side=2.0)

        # Should only draw 2 rectangles (filtered out the 1x1)
        assert mock_page.draw_rect.call_count == 2

    @patch('core.painter.fitz')
    def test_highlight_links_no_links(self, mock_fitz):
        """Test highlight_links with no links."""
        mock_doc = Mock()
        annots = []

        # Should handle empty list gracefully
        highlight_links(mock_doc, annots)

        # No pages should be accessed
        mock_doc.__getitem__.assert_not_called()

    @patch('core.painter.fitz')
    def test_highlight_links_page_out_of_range(self, mock_fitz):
        """Test highlight_links with page index out of range."""
        mock_doc = Mock()
        mock_doc.__len__.return_value = 1  # Only 1 page

        # Annotation for page 2 (index 1), but doc only has 1 page
        annots = [LinkAnnot(1, (0, 0, 10, 10), "uri", {})]

        # Should handle gracefully without crashing
        highlight_links(mock_doc, annots)

        # Should not try to access page 1
        mock_doc.__getitem__.assert_not_called()