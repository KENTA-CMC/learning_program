"""I/O utilities for PDF processing, batch operations, and safe file handling."""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("PyMuPDF is required. Install with: uv add pymupdf")

logger = logging.getLogger(__name__)


def open_doc(path: Union[str, Path], password: Optional[str] = None) -> fitz.Document:
    """Open a PDF document with optional password.

    Args:
        path: Path to PDF file
        password: Optional password for encrypted PDFs

    Returns:
        PyMuPDF Document object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a valid PDF
        RuntimeError: If password is incorrect or other PDF errors
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    try:
        doc = fitz.open(str(path))

        # Check if document is encrypted and handle password
        if doc.needs_pass:
            if password is None:
                raise RuntimeError("PDF is encrypted but no password provided")

            # Try to authenticate with password
            if not doc.authenticate(password):
                raise RuntimeError("Incorrect password for encrypted PDF")

        # Verify it's a valid PDF with pages
        if len(doc) == 0:
            raise ValueError("PDF has no pages")

        logger.info(f"Successfully opened PDF: {path} ({len(doc)} pages)")
        return doc

    except RuntimeError as e:
        if "password" in str(e).lower():
            raise RuntimeError(f"Failed to open encrypted PDF: {e}")
        else:
            raise RuntimeError(f"Failed to open PDF: {e}")

    except Exception as e:
        raise ValueError(f"Invalid PDF file: {e}")


def save_doc(doc: fitz.Document, out_path: Union[str, Path], overwrite: bool = False) -> None:
    """Save PDF document with atomic write and compression.

    Uses temporary file and atomic rename for safe saving.

    Args:
        doc: PyMuPDF Document object to save
        out_path: Output file path
        overwrite: Allow overwriting existing files

    Raises:
        FileExistsError: If output file exists and overwrite is False
        OSError: If save operation fails
    """
    out_path = Path(out_path)

    # Check if output file exists and overwrite policy
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"Output file exists (use --overwrite): {out_path}")

    # Create output directory if needed
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use temporary file for atomic save
    with tempfile.NamedTemporaryFile(
        suffix='.pdf',
        dir=out_path.parent,
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        # Save with compression
        doc.save(
            str(temp_path),
            deflate=True,        # Compress streams
            incremental=False,   # Full rewrite for smaller size
            ascii=False,         # Binary encoding
            expand=False,        # Keep compressed
            garbage=4            # Remove unused objects
        )

        # Atomic rename
        shutil.move(str(temp_path), str(out_path))

        logger.info(f"Successfully saved PDF: {out_path}")

    except Exception as e:
        # Clean up temporary file on error
        if temp_path.exists():
            temp_path.unlink()
        raise OSError(f"Failed to save PDF: {e}")


def generate_output_path(input_path: Union[str, Path], suffix: str = "_hl") -> Path:
    """Generate output path with suffix.

    Args:
        input_path: Input file path
        suffix: Suffix to add before file extension

    Returns:
        Output path with suffix

    Example:
        >>> generate_output_path("document.pdf", "_hl")
        Path("document_hl.pdf")
    """
    input_path = Path(input_path)
    stem = input_path.stem  # filename without extension
    ext = input_path.suffix  # file extension
    return input_path.parent / f"{stem}{suffix}{ext}"


def find_pdf_files(directory: Union[str, Path], recursive: bool = True) -> List[Path]:
    """Find all PDF files in a directory.

    Args:
        directory: Directory to search
        recursive: Search subdirectories recursively

    Returns:
        List of PDF file paths

    Raises:
        NotADirectoryError: If directory doesn't exist or is not a directory
    """
    directory = Path(directory)

    if not directory.exists():
        raise NotADirectoryError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdf_files = list(directory.glob(pattern))

    # Filter out non-files (just in case)
    pdf_files = [f for f in pdf_files if f.is_file()]

    logger.info(f"Found {len(pdf_files)} PDF files in {directory}")
    return sorted(pdf_files)


def process_batch(
    pdf_files: List[Path],
    processor_func,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Process multiple PDF files with a processor function.

    Args:
        pdf_files: List of PDF file paths
        processor_func: Function to process each PDF (takes path as first arg)
        *args: Additional positional arguments for processor_func
        **kwargs: Additional keyword arguments for processor_func

    Returns:
        Dictionary with processing results and statistics
    """
    results = {
        "processed": [],
        "failed": [],
        "total": len(pdf_files),
        "success_count": 0,
        "error_count": 0
    }

    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing: {pdf_path}")
            result = processor_func(pdf_path, *args, **kwargs)

            results["processed"].append({
                "path": str(pdf_path),
                "result": result
            })
            results["success_count"] += 1

        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")

            results["failed"].append({
                "path": str(pdf_path),
                "error": str(e)
            })
            results["error_count"] += 1

    logger.info(
        f"Batch processing complete: "
        f"{results['success_count']} success, "
        f"{results['error_count']} failed"
    )

    return results


def save_report_json(report: Dict[str, Any], report_path: Union[str, Path]) -> None:
    """Save processing report to JSON file.

    Args:
        report: Report dictionary to save
        report_path: Output JSON file path

    Raises:
        OSError: If file write fails
    """
    report_path = Path(report_path)

    try:
        # Ensure parent directory exists
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with report_path.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved: {report_path}")

    except Exception as e:
        raise OSError(f"Failed to save report: {e}")


def get_file_size(path: Union[str, Path]) -> int:
    """Get file size in bytes.

    Args:
        path: File path

    Returns:
        File size in bytes
    """
    return Path(path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"