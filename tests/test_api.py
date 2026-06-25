import io
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter
from pdf_editor.api.app import app

client = TestClient(app)


def make_pdf_bytes(pages: int = 2) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class TestRotateAPI:
    def test_rotate_returns_pdf(self):
        pdf = make_pdf_bytes(3)
        response = client.post(
            "/api/rotate",
            data={"pages": "1,2", "angle": "90"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_rotate_output_has_correct_page_count(self):
        pdf = make_pdf_bytes(4)
        response = client.post(
            "/api/rotate",
            data={"pages": "1,3", "angle": "90"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        reader = PdfReader(io.BytesIO(response.content))
        assert len(reader.pages) == 4

    def test_rotate_response_has_filename(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/rotate",
            data={"pages": "1", "angle": "90"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert "rotated.pdf" in response.headers.get("content-disposition", "")

    def test_rotate_invalid_pages_returns_422(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/rotate",
            data={"pages": "not,numbers", "angle": "90"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 422

    def test_rotate_missing_file_returns_422(self):
        response = client.post("/api/rotate", data={"pages": "1", "angle": "90"})
        assert response.status_code == 422

    def test_rotate_missing_pages_returns_422(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/rotate",
            data={"angle": "90"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 422

    def test_rotate_default_angle(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/rotate",
            data={"pages": "1"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200


class TestMergeAPI:
    def test_merge_returns_pdf(self):
        pdf1 = make_pdf_bytes(2)
        pdf2 = make_pdf_bytes(3)
        response = client.post(
            "/api/merge",
            files={
                "file1": ("a.pdf", pdf1, "application/pdf"),
                "file2": ("b.pdf", pdf2, "application/pdf"),
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_merge_output_has_correct_page_count(self):
        pdf1 = make_pdf_bytes(2)
        pdf2 = make_pdf_bytes(3)
        response = client.post(
            "/api/merge",
            files={
                "file1": ("a.pdf", pdf1, "application/pdf"),
                "file2": ("b.pdf", pdf2, "application/pdf"),
            },
        )
        assert response.status_code == 200
        reader = PdfReader(io.BytesIO(response.content))
        assert len(reader.pages) == 5

    def test_merge_missing_file2_returns_422(self):
        pdf1 = make_pdf_bytes(2)
        response = client.post(
            "/api/merge",
            files={"file1": ("a.pdf", pdf1, "application/pdf")},
        )
        assert response.status_code == 422

    def test_merge_missing_both_files_returns_422(self):
        response = client.post("/api/merge")
        assert response.status_code == 422


class TestOrderAPI:
    def test_order_returns_pdf(self):
        pdf = make_pdf_bytes(4)
        response = client.post(
            "/api/order",
            data={"num_pages": "4", "new_order": "4,3,2,1"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_order_output_has_correct_page_count(self):
        pdf = make_pdf_bytes(4)
        response = client.post(
            "/api/order",
            data={"num_pages": "4", "new_order": "4,3,2,1"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        reader = PdfReader(io.BytesIO(response.content))
        assert len(reader.pages) == 4

    def test_order_partial_reorder_preserves_all_pages(self):
        pdf = make_pdf_bytes(6)
        response = client.post(
            "/api/order",
            data={"num_pages": "3", "new_order": "3,2,1"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        reader = PdfReader(io.BytesIO(response.content))
        assert len(reader.pages) == 6

    def test_order_invalid_order_returns_500(self):
        pdf = make_pdf_bytes(4)
        response = client.post(
            "/api/order",
            data={"num_pages": "4", "new_order": "1,1,3,4"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 500

    def test_order_num_pages_exceeds_pdf_returns_500(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/order",
            data={"num_pages": "5", "new_order": "1,2,3,4,5"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 500

    def test_order_missing_num_pages_returns_422(self):
        pdf = make_pdf_bytes(3)
        response = client.post(
            "/api/order",
            data={"new_order": "1,2,3"},
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 422

    def test_order_missing_file_returns_422(self):
        response = client.post(
            "/api/order",
            data={"num_pages": "3", "new_order": "1,2,3"},
        )
        assert response.status_code == 422


class TestConvertAPI:
    def test_convert_returns_docx(self):
        pdf = make_pdf_bytes(1)
        response = client.post(
            "/api/convert",
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert "wordprocessingml" in response.headers["content-type"]

    def test_convert_response_has_filename(self):
        pdf = make_pdf_bytes(1)
        response = client.post(
            "/api/convert",
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert "converted.docx" in response.headers.get("content-disposition", "")

    def test_convert_missing_file_returns_422(self):
        response = client.post("/api/convert")
        assert response.status_code == 422
