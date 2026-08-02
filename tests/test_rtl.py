"""Unit tests for right-to-left detection and text-order repair."""

import os
import tempfile

import fitz
import pytest

from pdf_editor.rtl import (
    build_line_corrections,
    has_rtl,
    is_rtl_char,
    normalize,
    pdf_has_rtl,
    reorder_line,
)


def chars_from(pairs: list[tuple[str, float]], width: float = 5.0) -> list[dict]:
    """
    Builds PyMuPDF-shaped character dicts from (character, x-position) pairs.

    Args:
        pairs: Each character paired with the x coordinate of its left edge.
        width: Advance width to give every character.
    """
    return [
        {"c": char, "bbox": (x, 0.0, x + width, 10.0)}
        for char, x in pairs
    ]


def chars_spanning(triples: list[tuple[str, float, float]]) -> list[dict]:
    """
    Builds character dicts from explicit (character, left, right) triples.

    Used where a test needs the real, unevenly spaced geometry that MuPDF
    reported for a specific line rather than a synthetic approximation.
    """
    return [
        {"c": char, "bbox": (left, 0.0, right, 10.0)}
        for char, left, right in triples
    ]


# The base-14 PDF fonts have no Hebrew glyphs, so writing Hebrew into a test
# PDF needs a font from the system.
HEBREW_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
)

HEBREW_FONT = next((p for p in HEBREW_FONT_CANDIDATES if os.path.exists(p)), None)

needs_hebrew_font = pytest.mark.skipif(
    HEBREW_FONT is None,
    reason="no Hebrew-capable font found on this system",
)


def make_pdf(text: str, path: str) -> None:
    """Writes a one-page PDF containing `text`."""
    doc = fitz.open()
    page = doc.new_page()
    if HEBREW_FONT and has_rtl(text):
        page.insert_font(fontname="rtlfont", fontfile=HEBREW_FONT)
        page.insert_text((72, 72), text, fontname="rtlfont", fontsize=12)
    else:
        page.insert_text((72, 72), text, fontname="helv", fontsize=12)
    doc.save(path)
    doc.close()


class TestRTLDetection:
    def test_is_rtl_char_hebrew(self):
        assert is_rtl_char("א")
        assert is_rtl_char("ת")

    def test_is_rtl_char_arabic(self):
        assert is_rtl_char("ا")
        assert is_rtl_char("ي")

    def test_is_rtl_char_latin_and_digits(self):
        assert not is_rtl_char("a")
        assert not is_rtl_char("Z")
        assert not is_rtl_char("7")
        assert not is_rtl_char(":")

    def test_has_rtl(self):
        assert has_rtl("שלום")
        assert has_rtl("order 66 שלום")
        assert not has_rtl("plain ascii, 123")
        assert not has_rtl("")

    @needs_hebrew_font
    def test_pdf_has_rtl_on_hebrew_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            make_pdf("שלום עולם", path)
            assert pdf_has_rtl(path)
        finally:
            os.unlink(path)

    def test_pdf_has_rtl_on_ascii_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            make_pdf("Hello world, this is English text.", path)
            assert not pdf_has_rtl(path)
        finally:
            os.unlink(path)

    @needs_hebrew_font
    def test_pdf_has_rtl_ignores_a_stray_character(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            make_pdf("A long line of English prose with one letter: א", path)
            assert not pdf_has_rtl(path)
        finally:
            os.unlink(path)

    def test_pdf_has_rtl_on_empty_pdf(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            doc = fitz.open()
            doc.new_page()
            doc.save(path)
            doc.close()
            assert not pdf_has_rtl(path)
        finally:
            os.unlink(path)


class TestReorderLine:
    def test_empty_line(self):
        assert reorder_line([]) == ""

    def test_ltr_line_is_untouched(self):
        chars = chars_from([("a", 0), ("b", 5), ("c", 10), (":", 15)])
        assert reorder_line(chars) == "abc:"

    def test_trailing_colon_moves_to_the_end(self):
        # Rendered right-to-left, the colon sits to the left of the Hebrew, so
        # MuPDF emits it first even though it belongs at the end.
        chars = chars_from([(":", 442), ("נ", 480), ("ו", 470), ("ן", 460)])
        assert reorder_line(chars) == "נון:"

    def test_colon_and_digits_after_rtl_label(self):
        # From pay-2026-heb.pdf: " :טל03-9377218" should read "טל: 03-9377218".
        chars = chars_from(
            [(" ", 334), (":", 337), ("ט", 346), ("ל", 341)]
            + [(c, 276 + 6 * i) for i, c in enumerate("03-9377218")]
        )
        assert reorder_line(chars) == "טל: 03-9377218"

    def test_digits_keep_their_internal_order(self):
        chars = chars_from(
            [(c, 100 + 6 * i) for i, c in enumerate("2026")]
            + [("ש", 160), ("נ", 152), ("ה", 144)]
        )
        assert reorder_line(chars) == "שנה2026"

    def test_word_split_by_a_misplaced_neutral_is_rejoined(self):
        # Real geometry from pay-2026-heb.pdf, where a stray " :" landed in the
        # middle of "בועדה" and split the word in two.
        chars = chars_spanning([
            ("ב", 432.0, 438.3),
            ("ו", 429.0, 432.0),
            (" ", 403.5, 406.6),
            (":", 406.5, 410.2),
            ("ע", 422.9, 428.9),
            ("ד", 416.9, 423.0),
            ("ה", 410.1, 416.9),
        ])
        assert "".join(c["c"] for c in chars) == "בו :עדה"
        assert reorder_line(chars) == "בועדה: "

    def test_line_without_rtl_is_returned_verbatim(self):
        chars = chars_from([("9", 50), ("8", 40), ("7", 30)])
        assert reorder_line(chars) == "987"


class TestNormalize:
    def test_collapses_and_strips_whitespace(self):
        assert normalize("  a   b  ") == "a b"
        assert normalize("a\n\tb") == "a b"
        assert normalize("") == ""


class TestBuildLineCorrections:
    def test_ascii_pdf_yields_no_corrections(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            make_pdf("Nothing to correct here.", path)
            assert build_line_corrections(path) == {}
        finally:
            os.unlink(path)

    @needs_hebrew_font
    def test_corrections_map_to_different_text(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            make_pdf("שלום עולם", path)
            corrections = build_line_corrections(path)
            # Whatever it finds, an entry must never map text to itself.
            for original, corrected in corrections.items():
                assert original != corrected
        finally:
            os.unlink(path)
