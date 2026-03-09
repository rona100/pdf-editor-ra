"""PDF operations module for rotating and merging PDF files."""

from pypdf import PdfReader, PdfWriter
from pdf2docx import Converter


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


def convert_pdf_to_docx(input_path: str, output_path: str) -> None:
    """
    Converts a PDF file to a Word DOCX document.

    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the output DOCX file
    """
    # Create converter object
    cv = Converter(input_path)

    # Convert PDF to DOCX
    cv.convert(output_path, start=0, end=None)

    # Close the converter
    cv.close()

    print(f"Successfully converted '{input_path}' to DOCX format and saved as '{output_path}'")