import io
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
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

    def test_rotate_invalid_pages_returns_422(self):
        pdf = make_pdf_bytes(2)
        response = client.post(
            "/api/rotate",
            data={"pages": "not,numbers", "angle": "90"},
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


class TestConvertAPI:
    def test_convert_returns_docx(self):
        pdf = make_pdf_bytes(1)
        response = client.post(
            "/api/convert",
            files={"file": ("test.pdf", pdf, "application/pdf")},
        )
        assert response.status_code == 200
        assert "wordprocessingml" in response.headers["content-type"]
