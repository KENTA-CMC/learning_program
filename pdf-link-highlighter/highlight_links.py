#!/usr/bin/env python3
"""CLI interface for PDF link highlighting."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

from core import (
    open_doc, save_doc, detect_links, highlight_links, parse_color_string,
    generate_output_path, find_pdf_files, process_batch, get_link_statistics
)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PDF Link Highlighter - Automatically highlight link areas in PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python highlight_links.py --input document.pdf
  python highlight_links.py --input doc.pdf --output highlighted.pdf --color "#FFFF00"
  python highlight_links.py --batch ./pdfs --opacity 0.4 --mode draw
  python highlight_links.py --input doc.pdf --password secret --overwrite
        """
    )

    # Input/Output options
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Input PDF path (omit if using --batch)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output PDF path (default: <input>_hl.pdf)"
    )

    parser.add_argument(
        "--batch", "-b",
        type=str,
        help="Batch directory (recursive search for PDFs)"
    )

    # Highlighting options
    parser.add_argument(
        "--color", "-c",
        type=str,
        default="1,1,0",
        help="Highlight color (#RRGGBB or r,g,b). Default: 1,1,0 (yellow)"
    )

    parser.add_argument(
        "--opacity",
        type=float,
        default=0.35,
        help="Fill opacity (0.0-1.0). Default: 0.35"
    )

    parser.add_argument(
        "--mode",
        choices=["draw", "annot"],
        default="draw",
        help="Highlighting mode: 'draw' (recommended) or 'annot'. Default: draw"
    )

    parser.add_argument(
        "--min-side",
        type=float,
        default=2.0,
        help="Minimum short side in points (filters small links). Default: 2.0"
    )

    # Security options
    parser.add_argument(
        "--password", "-p",
        type=str,
        help="PDF password if encrypted"
    )

    # File handling options
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output files if they exist"
    )

    parser.add_argument(
        "--report-json",
        type=str,
        help="Save detection summary to JSON file"
    )

    # Other options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    # Input validation
    if not args.input and not args.batch:
        raise ValueError("Must specify either --input or --batch")

    if args.input and args.batch:
        raise ValueError("Cannot specify both --input and --batch")

    # Color validation
    if args.color:
        try:
            parse_color_string(args.color)
        except ValueError as e:
            raise ValueError(f"Invalid color format: {e}")

    # Opacity validation
    if not 0.0 <= args.opacity <= 1.0:
        raise ValueError("Opacity must be between 0.0 and 1.0")

    # Min side validation
    if args.min_side < 0:
        raise ValueError("Minimum side must be non-negative")


def process_single_pdf(
    input_path: Path,
    output_path: Optional[Path] = None,
    color: Tuple[float, float, float] = (1, 1, 0),
    opacity: float = 0.35,
    mode: str = "draw",
    min_side: float = 2.0,
    password: Optional[str] = None,
    overwrite: bool = False
) -> dict:
    """Process a single PDF file.

    Returns:
        Dictionary with processing results
    """
    logger = logging.getLogger(__name__)

    # Generate output path if not provided
    if output_path is None:
        output_path = generate_output_path(input_path)

    logger.info(f"Processing: {input_path}")
    logger.info(f"Output: {output_path}")

    # Open document
    doc = open_doc(input_path, password)

    try:
        # Detect links
        logger.info("Detecting links...")
        annots = detect_links(doc)

        if not annots:
            logger.warning("No links found in PDF")
            return {
                "input_path": str(input_path),
                "output_path": str(output_path),
                "links_detected": 0,
                "links_highlighted": 0,
                "statistics": {}
            }

        # Get statistics before filtering
        stats = get_link_statistics(annots)
        logger.info(f"Detected {len(annots)} links: {dict(stats['by_kind'])}")

        # Highlight links
        logger.info("Highlighting links...")
        highlight_links(
            doc,
            annots,
            color=color,
            opacity=opacity,
            mode=mode,
            min_side=min_side
        )

        # Count links after filtering
        filtered_count = len([a for a in annots if a.passes_min_side_filter(min_side)])

        # Save document
        logger.info("Saving highlighted PDF...")
        save_doc(doc, output_path, overwrite)

        logger.info(f"Successfully processed: {input_path}")

        return {
            "input_path": str(input_path),
            "output_path": str(output_path),
            "links_detected": len(annots),
            "links_highlighted": filtered_count,
            "statistics": stats
        }

    finally:
        doc.close()


def main() -> int:
    """Main CLI entry point."""
    try:
        args = parse_arguments()
        validate_arguments(args)

        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)

        # Parse color
        color = parse_color_string(args.color)

        if args.input:
            # Single file processing
            input_path = Path(args.input)
            output_path = Path(args.output) if args.output else None

            result = process_single_pdf(
                input_path=input_path,
                output_path=output_path,
                color=color,
                opacity=args.opacity,
                mode=args.mode,
                min_side=args.min_side,
                password=args.password,
                overwrite=args.overwrite
            )

            # Save report if requested
            if args.report_json:
                report_data = {
                    "mode": "single",
                    "result": result,
                    "settings": {
                        "color": color,
                        "opacity": args.opacity,
                        "mode": args.mode,
                        "min_side": args.min_side
                    }
                }

                with open(args.report_json, 'w') as f:
                    json.dump(report_data, f, indent=2)

                logger.info(f"Report saved: {args.report_json}")

        else:
            # Batch processing
            batch_dir = Path(args.batch)
            pdf_files = find_pdf_files(batch_dir)

            if not pdf_files:
                logger.warning(f"No PDF files found in: {batch_dir}")
                return 0

            logger.info(f"Found {len(pdf_files)} PDF files for batch processing")

            # Process batch
            def batch_processor(pdf_path):
                return process_single_pdf(
                    input_path=pdf_path,
                    color=color,
                    opacity=args.opacity,
                    mode=args.mode,
                    min_side=args.min_side,
                    password=args.password,
                    overwrite=args.overwrite
                )

            batch_results = process_batch(pdf_files, batch_processor)

            # Save batch report if requested
            if args.report_json:
                report_data = {
                    "mode": "batch",
                    "batch_directory": str(batch_dir),
                    "results": batch_results,
                    "settings": {
                        "color": color,
                        "opacity": args.opacity,
                        "mode": args.mode,
                        "min_side": args.min_side
                    }
                }

                with open(args.report_json, 'w') as f:
                    json.dump(report_data, f, indent=2)

                logger.info(f"Batch report saved: {args.report_json}")

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except RuntimeError as e:
        if "password" in str(e).lower():
            print(f"Error: {e}", file=sys.stderr)
            return 3
        else:
            print(f"Error: {e}", file=sys.stderr)
            return 2

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())