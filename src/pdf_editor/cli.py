"""Command-line interface for PDF Editor."""

import argparse
import sys
from .pdf_operations import merge_pdfs, rotate_pdf_pages, convert_pdf_to_docx


def main() -> None:
    """Main entry point for the PDF Editor CLI."""
    parser = argparse.ArgumentParser(
        description="PDF Editor - Rotate pages, merge PDF files, or convert to DOCX",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Rotate command
    rotate_parser = subparsers.add_parser(
        'rotate',
        help='Rotate specific pages in a PDF file',
        description="Rotate specified pages in a PDF file by 90, 180, or 270 degrees.",
        epilog="""
EXAMPLES:
  Rotate pages 1 and 2 by 180 degrees (default):
    python -m pdf_editor rotate original.pdf rotated.pdf 1,2

  Rotate pages 3, 5, and 7 by 90 degrees clockwise:
    python -m pdf_editor rotate original.pdf rotated.pdf 3,5,7 --angle 90

  Rotate page 10 by 270 degrees clockwise:
    python -m pdf_editor rotate original.pdf rotated.pdf 10 -a 270

NOTES:
  - Page numbers use 1-based indexing (first page is 1, not 0)
  - Separate multiple pages with commas (no spaces required, but allowed)
  - Rotation is always clockwise
  - The original PDF is not modified; output is saved to a new file
  - If output file exists, it will be overwritten
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    rotate_parser.add_argument(
        "input_pdf",
        help="Path to the input PDF file"
    )
    rotate_parser.add_argument(
        "output_pdf",
        help="Path to save the output PDF file"
    )
    rotate_parser.add_argument(
        "pages",
        type=str,
        help="Page numbers to rotate (comma-separated, e.g., 1,2,3)"
    )
    rotate_parser.add_argument(
        "-a", "--angle",
        type=int,
        default=180,
        choices=[90, 180, 270],
        help="Rotation angle in degrees (default: 180)"
    )

    # Merge command
    merge_parser = subparsers.add_parser(
        'merge',
        help='Merge two PDF files into one',
        description="Merge two PDF files into a single PDF file.",
        epilog="""
EXAMPLES:
  Merge two PDF files:
    python -m pdf_editor merge file1.pdf file2.pdf merged.pdf

  Combine a report with an appendix:
    python -m pdf_editor merge report.pdf appendix.pdf complete_report.pdf

NOTES:
  - Pages from the first PDF come first, followed by pages from the second PDF
  - The original PDF files are not modified
  - If output file exists, it will be overwritten
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    merge_parser.add_argument(
        "file1",
        help="Path to the first PDF file"
    )
    merge_parser.add_argument(
        "file2",
        help="Path to the second PDF file"
    )
    merge_parser.add_argument(
        "output_pdf",
        help="Path to save the merged PDF file"
    )

    # Convert command
    convert_parser = subparsers.add_parser(
        'convert',
        help='Convert a PDF file to Word DOCX format',
        description="Convert a PDF file to Microsoft Word DOCX format.",
        epilog="""
EXAMPLES:
  Convert a PDF to DOCX:
    python -m pdf_editor convert document.pdf document.docx

  Convert a scanned PDF (may have lower quality):
    python -m pdf_editor convert scanned.pdf scanned.docx

NOTES:
  - The conversion preserves text, formatting, and layout as much as possible
  - Image-based PDFs may have lower conversion quality
  - The original PDF file is not modified
  - If output file exists, it will be overwritten
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    convert_parser.add_argument(
        "input_pdf",
        help="Path to the input PDF file"
    )
    convert_parser.add_argument(
        "output_docx",
        help="Path to save the output DOCX file"
    )

    args = parser.parse_args()

    if args.command == 'rotate':
        # Parse page numbers from comma-separated string
        try:
            pages_to_rotate = [int(p.strip()) for p in args.pages.split(",")]
        except ValueError:
            print("Error: Pages must be comma-separated integers (e.g., 1,2,3)")
            sys.exit(1)

        # Call the rotate function
        rotate_pdf_pages(args.input_pdf, args.output_pdf, pages_to_rotate, args.angle)

    elif args.command == 'merge':
        # Call the merge function
        merge_pdfs(args.file1, args.file2, args.output_pdf)

    elif args.command == 'convert':
        # Call the convert function
        convert_pdf_to_docx(args.input_pdf, args.output_docx)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()