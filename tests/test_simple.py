#!/usr/bin/env python3
"""
Simple test script to verify PDF operations work correctly.
This script creates test PDFs and runs basic operations.
"""

import tempfile
import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter

# Import the functions to test
from pdf_editor.pdf_operations import rotate_pdf_pages, merge_pdfs


def create_test_pdf(pages=3):
    """Create a simple test PDF with specified number of pages."""
    writer = PdfWriter()
    for i in range(pages):
        writer.add_blank_page(width=612, height=792)  # Standard letter size

    temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
    with open(temp_file.name, 'wb') as f:
        writer.write(f)
    return temp_file.name


def test_rotate():
    input_pdf = create_test_pdf(pages=3)
    output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

    try:
        rotate_pdf_pages(input_pdf, output_pdf, [2], 90)

        with open(output_pdf, 'rb') as f:
            reader = PdfReader(f)
            assert len(reader.pages) == 3

    finally:
        if os.path.exists(input_pdf):
            os.unlink(input_pdf)
        if os.path.exists(output_pdf):
            os.unlink(output_pdf)


def test_merge():
    pdf1 = create_test_pdf(pages=2)
    pdf2 = create_test_pdf(pages=3)
    output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

    try:
        merge_pdfs(pdf1, pdf2, output_pdf)

        with open(output_pdf, 'rb') as f:
            reader = PdfReader(f)
            assert len(reader.pages) == 5

    finally:
        for pdf in [pdf1, pdf2, output_pdf]:
            if os.path.exists(pdf):
                os.unlink(pdf)


def main():
    """Run all tests."""
    print("Running PDF Editor Tests")
    print("=" * 30)

    results = []
    results.append(test_rotate())
    results.append(test_merge())

    print("\nTest Results:")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())