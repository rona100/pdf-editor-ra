"""PDF operations module for rotating and merging PDF files."""

from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from .docx_rtl import apply_rtl
from .rtl import build_line_corrections, pdf_has_rtl, reorder_line


def merge_pdfs(file1_path: str, file2_path: str, output_path: str) -> None:
    """
    Merges two PDF files into a single PDF.

    Args:
        file1_path (str): Path to the first PDF file
        file2_path (str): Path to the second PDF file
        output_path (str): Path to save the merged PDF file
    """
    writer = PdfWriter()

    # Add all pages from first PDF
    with open(file1_path, 'rb') as pdf1_file:
        reader1 = PdfReader(pdf1_file)
        for page in reader1.pages:
            writer.add_page(page)

    # Add all pages from second PDF
    with open(file2_path, 'rb') as pdf2_file:
        reader2 = PdfReader(pdf2_file)
        for page in reader2.pages:
            writer.add_page(page)

    # Write the merged PDF to output file
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    print(f"Successfully merged '{file1_path}' and '{file2_path}' into '{output_path}'")


def rotate_pdf_pages(input_path: str, output_path: str, pages_to_rotate: list[int], rotation_angle: int = 180) -> None:
    """
    Rotates specified pages in a PDF file by a given angle (90, 180, or 270 degrees).

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the output PDF file.
        pages_to_rotate (list of int): A list of page numbers (1-based) to rotate.
        rotation_angle (int): The clockwise rotation angle (90, 180, 270).
    """
    # Open the original PDF file
    with open(input_path, 'rb') as pdf_in_file:
        reader = PdfReader(pdf_in_file)
        writer = PdfWriter()

        # Iterate through all pages
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            # Check if the current page number is in the list to rotate (convert to 0-based index)
            if (page_num + 1) in pages_to_rotate:
                page.rotate(rotation_angle)
            writer.add_page(page)

        # Write the modified PDF to a new file
        with open(output_path, 'wb') as pdf_out_file:
            writer.write(pdf_out_file)

    print(f"Successfully rotated pages {pages_to_rotate} of '{input_path}' by {rotation_angle} degrees and saved as '{output_path}'")


def order_pdf_pages(input_path: str, output_path: str, num_pages: int, new_order: str) -> None:
    """
    Reorders the first N pages of a PDF file according to the specified order.

    Args:
        input_path (str): The path to the input PDF file.
        output_path (str): The path to save the output PDF file.
        num_pages (int): Number of pages to reorder from the beginning.
        new_order (str): Comma-separated list of page positions (e.g., '1,3,2,5,4,6').
    """
    with open(input_path, 'rb') as pdf_in_file:
        reader = PdfReader(pdf_in_file)
        total_pages = len(reader.pages)

        if num_pages > total_pages:
            raise ValueError(f"Cannot reorder {num_pages} pages: PDF only has {total_pages} pages")

        # Parse the new order
        try:
            order_list = [int(x.strip()) for x in new_order.split(',')]
        except ValueError as e:
            raise ValueError(f"Invalid new_order format: {e}. Expected comma-separated integers.")

        if len(order_list) != num_pages:
            raise ValueError(f"new_order must contain exactly {num_pages} page positions, got {len(order_list)}")

        # Validate that order_list contains each number from 1 to num_pages exactly once
        expected = set(range(1, num_pages + 1))
        actual = set(order_list)
        if expected != actual:
            raise ValueError(f"new_order must contain each number from 1 to {num_pages} exactly once. Got: {order_list}")

        # Create the reordered page list
        reordered_pages = []
        for pos in order_list:
            reordered_pages.append(reader.pages[pos - 1])  # Convert to 0-based index

        # Add any remaining pages in their original order
        for i in range(num_pages, total_pages):
            reordered_pages.append(reader.pages[i])

        # Create new PDF with reordered pages
        writer = PdfWriter()
        for page in reordered_pages:
            writer.add_page(page)

        # Write the reordered PDF to output file
        with open(output_path, 'wb') as pdf_out_file:
            writer.write(pdf_out_file)

    print(f"Successfully reordered first {num_pages} pages of '{input_path}' according to '{new_order}' and saved as '{output_path}'")


RTL_MODES = ('auto', 'on', 'off')


def convert_pdf_to_docx(input_path: str, output_path: str, rtl: str = 'auto') -> None:
    """
    Converts a PDF file to a Word DOCX document.

    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the output DOCX file
        rtl (str): Right-to-left handling. 'auto' (default) detects Hebrew,
            Arabic and similar scripts in the PDF; 'on' forces the repair pass;
            'off' skips it entirely.
    """
    if rtl not in RTL_MODES:
        raise ValueError(f"rtl must be one of {RTL_MODES}, got {rtl!r}")

    use_rtl = rtl == 'on' or (rtl == 'auto' and pdf_has_rtl(input_path))

    try:
        # First try the standard pdf2docx conversion
        cv = Converter(input_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()

        if use_rtl:
            _repair_rtl(input_path, output_path)

        print(f"Successfully converted '{input_path}' to DOCX format and saved as '{output_path}'")

    except Exception as e:
        print(f"Standard conversion failed: {e}")
        print("Attempting fallback text extraction method...")

        try:
            # Fallback: Extract text using PyMuPDF and create a basic DOCX
            _fallback_text_extraction(input_path, output_path, rtl=use_rtl)
            print(f"Successfully converted '{input_path}' to DOCX format using fallback method and saved as '{output_path}'")

        except Exception as fallback_error:
            print(f"Fallback conversion also failed: {fallback_error}")
            raise RuntimeError(f"PDF conversion failed for '{input_path}'. The PDF may contain complex layouts or unsupported elements.")


def _repair_rtl(input_path: str, output_path: str) -> None:
    """
    Fixes text order and direction of right-to-left content in a converted DOCX.

    Failures here are reported but never raised: a successful conversion with
    unrepaired RTL text is still far more useful than no document at all.

    Args:
        input_path (str): Path to the source PDF file
        output_path (str): Path to the DOCX file to patch in place
    """
    try:
        corrections = build_line_corrections(input_path)
        stats = apply_rtl(output_path, corrections)
        print(
            f"Applied RTL repair: {stats['paragraphs']} paragraphs, "
            f"{stats['runs']} runs, {stats['text_fixed']} text fixes "
            f"({stats['text_unmatched']} unmatched)"
        )
    except Exception as e:
        print(f"RTL repair failed, leaving converted document as-is: {e}")


def _fallback_text_extraction(input_path: str, output_path: str, rtl: bool = False) -> None:
    """
    Fallback method that extracts text from PDF and creates a basic DOCX document.
    Useful for PDFs with complex layouts that pdf2docx can't handle.

    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the output DOCX file
        rtl (bool): Extract right-to-left text in logical order and mark the
            resulting paragraphs as RTL
    """
    # Create a new Word document
    doc = Document()
    doc.add_heading('PDF Content', 0)

    # Open PDF with PyMuPDF
    pdf_doc = fitz.open(input_path)

    try:
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]

            # Add page heading
            doc.add_heading(f'Page {page_num + 1}', level=1)

            # Extract text from the page
            text = _extract_rtl_text(page) if rtl else page.get_text()

            # Split text into paragraphs and add to document
            paragraphs = text.split('\n\n')
            for para_text in paragraphs:
                if para_text.strip():  # Only add non-empty paragraphs
                    doc.add_paragraph(para_text.strip())

            # Add page break between pages (except for the last page)
            if page_num < len(pdf_doc) - 1:
                doc.add_page_break()

    finally:
        pdf_doc.close()

    # Save the document
    doc.save(output_path)

    if rtl:
        # No correction table needed: the text is already in logical order, so
        # this pass only stamps the direction properties.
        try:
            apply_rtl(output_path)
        except Exception as e:
            print(f"RTL marking failed, leaving document as-is: {e}")


def _extract_rtl_text(page) -> str:
    """
    Extracts a page's text with right-to-left lines rebuilt in logical order.

    Args:
        page: A PyMuPDF page object

    Returns:
        str: The page text, one line per line, blocks separated by blank lines
    """
    blocks_text = []

    for block in page.get_text("rawdict")["blocks"]:
        if block.get("type") != 0:  # skip images
            continue
        lines = []
        for line in block["lines"]:
            chars = [c for span in line["spans"] for c in span["chars"]]
            lines.append(reorder_line(chars))
        if lines:
            blocks_text.append("\n".join(lines))

    return "\n\n".join(blocks_text)


def convert_docx_to_pdf(input_path: str, output_path: str, timeout: int = 120) -> None:
    """
    Converts a Word DOCX document to PDF using LibreOffice in headless mode.

    Args:
        input_path (str): Path to the input DOCX file
        output_path (str): Path to save the output PDF file
        timeout (int): Seconds to wait for LibreOffice before giving up
    """
    _check_is_docx(input_path)
    soffice = _find_soffice()

    with tempfile.TemporaryDirectory(prefix="pdf_editor_soffice_") as workdir:
        outdir = Path(workdir) / "out"
        outdir.mkdir()

        # Each conversion gets a private profile directory. Without this,
        # concurrent LibreOffice invocations contend for the shared user
        # profile and one of them hangs until the timeout expires.
        profile = Path(workdir) / "profile"

        command = [
            soffice,
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--norestore",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", str(outdir),
            str(input_path),
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"LibreOffice timed out after {timeout}s converting '{input_path}'"
            )

        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice failed to convert '{input_path}': "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

        # LibreOffice names the output after the input stem and ignores the
        # requested filename, and it can exit 0 having produced nothing at all.
        produced = list(outdir.glob("*.pdf"))
        if not produced:
            raise RuntimeError(
                f"LibreOffice produced no PDF for '{input_path}'. "
                "The file may be corrupt or not a Word document."
            )

        shutil.move(str(produced[0]), output_path)

    print(f"Successfully converted '{input_path}' to PDF and saved as '{output_path}'")


def _check_is_docx(input_path: str) -> None:
    """
    Raises ValueError unless `input_path` is really a Word document.

    LibreOffice sniffs content rather than trusting the extension, so handing
    it arbitrary bytes yields a PDF of those bytes rendered as plain text
    instead of an error. Checking up front keeps that from looking like a
    successful conversion.
    """
    try:
        with zipfile.ZipFile(input_path) as archive:
            names = set(archive.namelist())
    except (zipfile.BadZipFile, OSError):
        raise ValueError(
            f"'{input_path}' is not a Word document (expected a .docx file)"
        )

    if "word/document.xml" not in names:
        raise ValueError(
            f"'{input_path}' is a zip archive but not a Word document "
            "(no word/document.xml)"
        )


def _find_soffice() -> str:
    """Locates the LibreOffice binary, or explains how to install it."""
    candidate = os.environ.get("SOFFICE_BIN")
    if candidate and shutil.which(candidate):
        return candidate

    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found

    raise RuntimeError(
        "LibreOffice is required for DOCX to PDF conversion but was not found. "
        "Install it with 'apt-get install -y libreoffice-writer', or set "
        "SOFFICE_BIN to the binary's path."
    )