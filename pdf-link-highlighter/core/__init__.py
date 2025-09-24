"""Core module for PDF link highlighting functionality."""

from .annot_model import LinkAnnot
from .detector import detect_links, filter_by_min_side, get_link_statistics
from .painter import highlight_links, parse_color_string
from .io_utils import open_doc, save_doc, generate_output_path, find_pdf_files, process_batch

__all__ = [
    "LinkAnnot",
    "detect_links",
    "filter_by_min_side",
    "get_link_statistics",
    "highlight_links",
    "parse_color_string",
    "open_doc",
    "save_doc",
    "generate_output_path",
    "find_pdf_files",
    "process_batch",
]