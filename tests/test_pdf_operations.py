import pytest
import tempfile
import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter

# Import the functions to test
from pdf_editor.pdf_operations import rotate_pdf_pages, merge_pdfs, convert_pdf_to_docx, order_pdf_pages


class TestPDFOperations:
    """Test class for PDF rotation and merging operations."""

    def create_test_pdf(self, pages=3, content="Test Page"):
        """Create a simple test PDF with specified number of pages."""
        writer = PdfWriter()
        for i in range(pages):
            # Create a simple page (in a real scenario, you'd use a proper PDF library to create content)
            # For now, we'll create empty pages
            writer.add_blank_page(width=612, height=792)  # Standard letter size

        # Write to a temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        with open(temp_file.name, 'wb') as f:
            writer.write(f)
        return temp_file.name

    def test_rotate_pdf_pages_single_page(self):
        """Test rotating a single page in a PDF."""
        # Create a test PDF with 3 pages
        input_pdf = self.create_test_pdf(pages=3)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Rotate page 2 by 90 degrees
            rotate_pdf_pages(input_pdf, output_pdf, [2], 90)

            # Verify the output file exists
            assert os.path.exists(output_pdf)

            # Verify the PDF has the correct number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 3

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(input_pdf)

    def test_rotate_pdf_pages_multiple_pages(self):
        """Test rotating multiple pages in a PDF."""
        # Create a test PDF with 4 pages
        input_pdf = self.create_test_pdf(pages=4)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Rotate pages 1 and 3 by 180 degrees
            rotate_pdf_pages(input_pdf, output_pdf, [1, 3], 180)

            # Verify the output file exists
            assert os.path.exists(output_pdf)

            # Verify the PDF has the correct number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 4

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(input_pdf)

    def test_rotate_pdf_pages_invalid_page(self):
        """Test rotating a page number that doesn't exist."""
        # Create a test PDF with 2 pages
        input_pdf = self.create_test_pdf(pages=2)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Try to rotate page 5 (which doesn't exist)
            rotate_pdf_pages(input_pdf, output_pdf, [5], 90)

            # Verify the output file exists (should still be created)
            assert os.path.exists(output_pdf)

            # Verify the PDF has the correct number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 2  # Should have same number of pages

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(input_pdf)

    def test_merge_pdfs(self):
        """Test merging two PDF files."""
        # Create two test PDFs
        pdf1 = self.create_test_pdf(pages=2)
        pdf2 = self.create_test_pdf(pages=3)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Merge the PDFs
            merge_pdfs(pdf1, pdf2, output_pdf)

            # Verify the output file exists
            assert os.path.exists(output_pdf)

            # Verify the merged PDF has the correct total number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 5  # 2 + 3 pages

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(pdf1)
            os.unlink(pdf2)

    def test_merge_pdfs_empty_files(self):
        """Test merging PDFs with different page counts."""
        # Create two PDFs with different page counts
        pdf1 = self.create_test_pdf(pages=1)
        pdf2 = self.create_test_pdf(pages=4)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Merge the PDFs
            merge_pdfs(pdf1, pdf2, output_pdf)

            # Verify the output file exists
            assert os.path.exists(output_pdf)

            # Verify the merged PDF has the correct total number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 5  # 1 + 4 pages

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(pdf1)
            os.unlink(pdf2)

    def test_rotate_different_angles(self):
        """Test rotating pages with different angles."""
        # Create a test PDF
        input_pdf = self.create_test_pdf(pages=2)

        try:
            # Test different angles
            for angle in [90, 180, 270]:
                output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

                rotate_pdf_pages(input_pdf, output_pdf, [1], angle)

                # Verify the output file exists and has correct page count
                assert os.path.exists(output_pdf)
                with open(output_pdf, 'rb') as f:
                    reader = PdfReader(f)
                    assert len(reader.pages) == 2

                os.unlink(output_pdf)

        finally:
            os.unlink(input_pdf)


    def test_convert_pdf_to_docx(self):
        """Test converting a PDF to DOCX format."""
        # Create a test PDF
        input_pdf = self.create_test_pdf(pages=2)

        try:
            # Create output file
            output_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False).name

            # Convert PDF to DOCX
            convert_pdf_to_docx(input_pdf, output_docx)

            # Verify the output file exists
            assert os.path.exists(output_docx)

            # Verify it's a DOCX file (check file size > 0)
            assert os.path.getsize(output_docx) > 0

            # Clean up
            os.unlink(output_docx)

        finally:
            os.unlink(input_pdf)


    def test_order_pdf_pages(self):
        """Test reordering pages in a PDF."""
        # Create a test PDF with 6 pages
        input_pdf = self.create_test_pdf(pages=6)

        try:
            # Create output file
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name

            # Reorder first 6 pages as 1,3,2,5,4,6
            order_pdf_pages(input_pdf, output_pdf, 6, '1,3,2,5,4,6')

            # Verify the output file exists
            assert os.path.exists(output_pdf)

            # Verify the PDF has the correct number of pages
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 6

            # Clean up
            os.unlink(output_pdf)

        finally:
            os.unlink(input_pdf)

    def test_order_pdf_pages_partial(self):
        """Test reordering only some pages in a PDF."""
        input_pdf = self.create_test_pdf(pages=8)
        try:
            output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            order_pdf_pages(input_pdf, output_pdf, 4, '4,1,3,2')
            assert os.path.exists(output_pdf)
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 8
            os.unlink(output_pdf)
        finally:
            os.unlink(input_pdf)

    def test_rotate_verifies_rotation_metadata(self):
        """Verify rotated pages have the correct rotation value in PDF metadata."""
        input_pdf = self.create_test_pdf(pages=3)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            rotate_pdf_pages(input_pdf, output_pdf, [1, 3], 90)
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert reader.pages[0].rotation == 90
                assert reader.pages[1].rotation == 0
                assert reader.pages[2].rotation == 90
            os.unlink(output_pdf)
        finally:
            os.unlink(input_pdf)

    def test_rotate_270_degrees_metadata(self):
        """Verify 270-degree rotation is stored correctly in PDF metadata."""
        input_pdf = self.create_test_pdf(pages=2)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            rotate_pdf_pages(input_pdf, output_pdf, [2], 270)
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert reader.pages[0].rotation == 0
                assert reader.pages[1].rotation == 270
            os.unlink(output_pdf)
        finally:
            os.unlink(input_pdf)

    def test_order_raises_when_num_pages_exceeds_total(self):
        """order_pdf_pages raises ValueError when num_pages > total pages."""
        input_pdf = self.create_test_pdf(pages=3)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            with pytest.raises(ValueError, match="only has"):
                order_pdf_pages(input_pdf, output_pdf, 5, '1,2,3,4,5')
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_raises_when_order_has_wrong_count(self):
        """order_pdf_pages raises ValueError when new_order length != num_pages."""
        input_pdf = self.create_test_pdf(pages=4)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            with pytest.raises(ValueError, match="exactly"):
                order_pdf_pages(input_pdf, output_pdf, 4, '1,2,3')
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_raises_when_order_has_duplicates(self):
        """order_pdf_pages raises ValueError when new_order contains duplicate pages."""
        input_pdf = self.create_test_pdf(pages=4)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            with pytest.raises(ValueError, match="exactly once"):
                order_pdf_pages(input_pdf, output_pdf, 4, '1,1,3,4')
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_order_raises_when_order_not_integers(self):
        """order_pdf_pages raises ValueError when new_order contains non-integers."""
        input_pdf = self.create_test_pdf(pages=3)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            with pytest.raises(ValueError, match="Invalid new_order"):
                order_pdf_pages(input_pdf, output_pdf, 3, 'a,b,c')
        finally:
            os.unlink(input_pdf)
            if os.path.exists(output_pdf):
                os.unlink(output_pdf)

    def test_convert_output_is_valid_docx(self):
        """Verify convert_pdf_to_docx produces a valid, openable DOCX file."""
        from docx import Document
        input_pdf = self.create_test_pdf(pages=1)
        output_docx = tempfile.NamedTemporaryFile(suffix='.docx', delete=False).name
        try:
            convert_pdf_to_docx(input_pdf, output_docx)
            doc = Document(output_docx)
            assert doc is not None
            os.unlink(output_docx)
        finally:
            os.unlink(input_pdf)

    def test_merge_preserves_all_pages_accessible(self):
        """Verify every page of a merged PDF is accessible."""
        pdf1 = self.create_test_pdf(pages=3)
        pdf2 = self.create_test_pdf(pages=2)
        output_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        try:
            merge_pdfs(pdf1, pdf2, output_pdf)
            with open(output_pdf, 'rb') as f:
                reader = PdfReader(f)
                assert len(reader.pages) == 5
                for page in reader.pages:
                    assert page is not None
            os.unlink(output_pdf)
        finally:
            os.unlink(pdf1)
            os.unlink(pdf2)


if __name__ == "__main__":
    pytest.main([__file__])