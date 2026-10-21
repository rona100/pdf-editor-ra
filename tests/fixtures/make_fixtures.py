"""
Generates the synthetic PDFs in this directory.

They stand in for real documents when checking conversion quality, so that
nobody's personal files are needed to reproduce a layout or RTL problem.
Each one isolates a case pdf2docx or the RTL repair has struggled with.

Run from the repository root:
    .venv/bin/python tests/fixtures/make_fixtures.py
"""

from pathlib import Path

import fitz

HERE = Path(__file__).parent
PAGE = fitz.Rect(0, 0, 595, 842)  # A4
BODY = fitz.Rect(56, 56, 539, 786)

CSS = "body { font-family: sans-serif; font-size: 12pt; } p { margin: 0 0 8pt 0; }"


def _html_pdf(name: str, html: str, draw=None) -> None:
    """Lays out html on one A4 page; draw(page) may add shapes underneath."""
    doc = fitz.open()
    page = doc.new_page(width=PAGE.width, height=PAGE.height)
    if draw:
        draw(page)
    page.insert_htmlbox(BODY, html, css=CSS)
    doc.save(HERE / name, garbage=4, deflate=True)
    doc.close()


def ltr() -> None:
    _html_pdf(
        "ltr.pdf",
        "<h2>Quarterly report</h2>"
        "<p>This document is plain left-to-right English. Converting it must "
        "produce exactly the same DOCX as with RTL handling switched off.</p>"
        "<p>Second paragraph with numbers 1,234.56 and a date 2026-10-21.</p>",
    )


def hebrew() -> None:
    _html_pdf(
        "hebrew.pdf",
        '<div dir="rtl">'
        "<h2>דוח רבעוני</h2>"
        "<p>זהו מסמך בדיקה בעברית. הפסקה הראשונה מכילה משפט ארוך מספיק כדי "
        "להישבר על פני כמה שורות, כך שאפשר לבדוק את סדר השורות ואת היישור לימין.</p>"
        "<p>פסקה שנייה, קצרה יותר.</p>"
        "</div>",
    )


def mixed() -> None:
    _html_pdf(
        "mixed.pdf",
        '<div dir="rtl">'
        "<p>הסכום לתשלום הוא 1,234.56 ש\"ח עד לתאריך 21/10/2026.</p>"
        "<p>הקובץ נוצר בתוכנת PDF Editor גרסה 0.1.0 ונשלח אל ron@example.com.</p>"
        "<p>מספר טלפון: 03-1234567, מספר תיק (A-17).</p>"
        "</div>",
    )


def shaded_table() -> None:
    rows = [("פריט", "כמות", "מחיר"), ("עט", "3", "12.00"), ("מחברת", "5", "45.50")]
    cells = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows
    )

    def shade(page):
        # The shaded band behind the table is what pdf2docx tends to drop.
        page.draw_rect(fitz.Rect(56, 50, 539, 160), color=None, fill=(0.85, 0.9, 0.95))

    _html_pdf(
        "shaded_table.pdf",
        '<div dir="rtl"><p>טבלה על רקע צבעוני:</p>'
        '<table border="1" style="border-collapse: collapse; width: 100%">'
        f"{cells}</table></div>",
        draw=shade,
    )


def textbox() -> None:
    doc = fitz.open()
    page = doc.new_page(width=PAGE.width, height=PAGE.height)
    page.insert_htmlbox(
        fitz.Rect(56, 56, 539, 200),
        '<p dir="rtl">טקסט רגיל בגוף העמוד, מחוץ לתיבה.</p>',
        css=CSS,
    )
    # A framed, floating box beside body text; converters often lose these.
    box = fitz.Rect(330, 220, 539, 330)
    page.draw_rect(box, color=(0, 0, 0), fill=(1, 1, 0.85), width=1)
    page.insert_htmlbox(
        box + (8, 8, -8, -8),
        '<p dir="rtl">תיבת טקסט צפה עם הערה חשובה.</p>',
        css=CSS,
    )
    doc.save(HERE / "textbox.pdf", garbage=4, deflate=True)
    doc.close()


if __name__ == "__main__":
    for make in (ltr, hebrew, mixed, shaded_table, textbox):
        make()
        print(f"wrote {make.__name__}")
