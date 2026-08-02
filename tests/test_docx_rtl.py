"""Tests for the right-to-left repair pass applied to a generated DOCX."""

import os
import tempfile

from docx import Document
from docx.oxml.ns import qn

from pdf_editor.docx_rtl import apply_rtl


def make_docx(paragraphs: list[str], path: str) -> None:
    """Writes a DOCX containing one run per supplied paragraph."""
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    document.save(path)


def docx_xml(path: str) -> str:
    """Returns the document body XML as a string."""
    document = Document(path)
    return document.element.body.xml


def temp_docx() -> str:
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        return f.name


class TestApplyRtl:
    def test_marks_rtl_paragraphs_and_runs(self):
        path = temp_docx()
        try:
            make_docx(["שלום עולם"], path)
            stats = apply_rtl(path)

            assert stats["paragraphs"] == 1
            assert stats["runs"] == 1

            xml = docx_xml(path)
            assert "<w:bidi" in xml
            assert "<w:rtl" in xml
        finally:
            os.unlink(path)

    def test_leaves_ltr_documents_alone(self):
        path = temp_docx()
        try:
            make_docx(["Hello world", "Nothing to see here"], path)
            before = docx_xml(path)
            stats = apply_rtl(path)

            assert stats == {
                "paragraphs": 0,
                "runs": 0,
                "text_fixed": 0,
                "text_unmatched": 0,
            }
            assert docx_xml(path) == before
        finally:
            os.unlink(path)

    def test_substitutes_text_from_the_correction_table(self):
        path = temp_docx()
        try:
            make_docx([":נושא המחקר"], path)
            stats = apply_rtl(path, {":נושא המחקר": "נושא המחקר:"})

            assert stats["text_fixed"] == 1
            assert Document(path).paragraphs[0].text == "נושא המחקר:"
        finally:
            os.unlink(path)

    def test_matches_on_collapsed_whitespace_and_keeps_own_padding(self):
        path = temp_docx()
        try:
            make_docx(["  :שם החוקר "], path)
            # The table entry carries different padding than the run does.
            stats = apply_rtl(path, {":שם החוקר": "שם החוקר:      "})

            assert stats["text_fixed"] == 1
            assert Document(path).paragraphs[0].text == "  שם החוקר: "
        finally:
            os.unlink(path)

    def test_unmatched_text_is_left_untouched(self):
        path = temp_docx()
        try:
            make_docx(["טקסט שאין לו התאמה"], path)
            stats = apply_rtl(path, {"משהו אחר": "אחר משהו"})

            assert stats["text_fixed"] == 0
            assert stats["text_unmatched"] == 1
            assert Document(path).paragraphs[0].text == "טקסט שאין לו התאמה"
        finally:
            os.unlink(path)

    def test_reaches_paragraphs_inside_tables(self):
        path = temp_docx()
        try:
            document = Document()
            table = document.add_table(rows=1, cols=2)
            table.cell(0, 0).text = ":מחלקה"
            table.cell(0, 1).text = "Department"
            document.save(path)

            stats = apply_rtl(path, {":מחלקה": "מחלקה:"})

            assert stats["text_fixed"] == 1
            assert Document(path).tables[0].cell(0, 0).text == "מחלקה:"
            # The Latin cell must be left as it was.
            assert Document(path).tables[0].cell(0, 1).text == "Department"
        finally:
            os.unlink(path)

    def test_result_is_still_a_readable_docx(self):
        path = temp_docx()
        try:
            make_docx(["שלום", "Hello", "עולם 2026"], path)
            apply_rtl(path)

            document = Document(path)
            assert [p.text for p in document.paragraphs] == ["שלום", "Hello", "עולם 2026"]
        finally:
            os.unlink(path)

    def test_run_properties_mirror_to_complex_script(self):
        path = temp_docx()
        try:
            document = Document()
            run = document.add_paragraph().add_run("שלום")
            run.bold = True
            run.font.size = 152400  # 12pt in EMU
            document.save(path)

            apply_rtl(path)

            rPr = Document(path).paragraphs[0].runs[0]._element.find(qn("w:rPr"))
            assert rPr.find(qn("w:rtl")) is not None
            assert rPr.find(qn("w:bCs")) is not None
            assert rPr.find(qn("w:szCs")) is not None
        finally:
            os.unlink(path)

    def test_is_idempotent(self):
        path = temp_docx()
        try:
            make_docx(["שלום עולם"], path)
            apply_rtl(path)
            first = docx_xml(path)
            apply_rtl(path)

            assert docx_xml(path) == first
        finally:
            os.unlink(path)
