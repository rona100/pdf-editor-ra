# PDF Editor

A dual-mode application for manipulating PDF files — run it from the **command line** or use the **browser-based web interface**.

Supported operations:
- **Rotate** specific pages by 90, 180, or 270 degrees
- **Merge** two PDF files into one
- **Reorder** pages using a position mapping
- **Convert** PDFs to Microsoft Word DOCX format, with right-to-left (Hebrew, Arabic) repair
- **Convert** DOCX files back to PDF
- **Sanitize** a PDF: rebuild every page as an image with a fresh OCR text layer and blank metadata,
  or (`--mode basic`) strip metadata, annotations and hidden text while keeping the original text,
  or (`--mode ats`) also rebuild the text so applicant tracking systems read it in order

## Quick Start

### Docker (Recommended — no Node.js required)

```bash
docker-compose up --build
```

Open **http://localhost:8000** in your browser.

### CLI

```bash
# Install
uv pip install -e .

# Rotate pages 1 and 2 by 180 degrees
uv run python -m pdf_editor rotate document.pdf 1,2 -o rotated.pdf

# Merge two PDFs
uv run python -m pdf_editor merge file1.pdf file2.pdf -o merged.pdf

# Reorder first 6 pages
uv run python -m pdf_editor order document.pdf 6 1,3,2,5,4,6 -o reordered.pdf

# Convert to DOCX
uv run python -m pdf_editor convert document.pdf -o output.docx

# Convert DOCX back to PDF (requires LibreOffice)
uv run python -m pdf_editor docx2pdf document.docx -o output.pdf

# Sanitize: rasterize + OCR, strip hidden data and metadata (requires Tesseract)
uv run python -m pdf_editor sanitize document.pdf -o clean.pdf

# Sanitize without OCR: strip metadata, annotations and hidden text only
uv run python -m pdf_editor sanitize document.pdf -o clean.pdf --mode basic

# Prepare a CV for applicant tracking systems: hidden data removed, text in reading order
uv run python -m pdf_editor sanitize cv.pdf -o cv-clean.pdf --mode ats
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended)
- Docker (for web mode without Node.js)
- Node.js 18+ (only for frontend development)
- LibreOffice (only for DOCX→PDF): `sudo apt-get install -y libreoffice-writer`.
  Already included in the Docker image. Set `SOFFICE_BIN` if the binary is not on `PATH`.
- Tesseract (only for sanitize in the default `ocr` mode): `sudo apt-get install -y tesseract-ocr tesseract-ocr-heb`
  (macOS: `brew install tesseract tesseract-lang`). Already included in the Docker image.
  Set `TESSERACT_CMD` if the binary is not on `PATH`.

## Installation

```bash
# CLI only
uv pip install -e .

# CLI + web server
uv pip install -e ".[web]"

# CLI + web server + dev/test tools
uv pip install -e ".[web,dev]"
```

## CLI Usage

```bash
# Rotate: pages are 1-based, angle defaults to 180
uv run python -m pdf_editor rotate <input> <pages> -o <output> [--angle 90|180|270]

# Merge
uv run python -m pdf_editor merge <file1> <file2> -o <output>

# Reorder: new_order is a permutation of 1..num_pages
uv run python -m pdf_editor order <input> <num_pages> <new_order> -o <output>

# Convert to DOCX; --rtl is auto|on|off (default auto)
uv run python -m pdf_editor convert <input> -o <output> [--rtl auto|on|off]

# Convert DOCX to PDF
uv run python -m pdf_editor docx2pdf <input> -o <output> [--timeout 120]

# Sanitize a PDF (OCR languages default to eng+heb)
uv run python -m pdf_editor sanitize <input> -o <output> [--mode ocr|basic|ats] [--lang eng+heb] [--dpi 300]

# Help
uv run python -m pdf_editor --help
uv run python -m pdf_editor <operation> --help
```

## Web Mode

### Docker (no Node.js needed)

```bash
# Build and run
docker-compose up --build

# Rebuild after code changes
docker-compose up --build

# Stop
docker-compose down
```

Open **http://localhost:8000**.

### Development (with Node.js)

Terminal 1 — Backend:
```bash
uv run uvicorn pdf_editor.api.app:app --reload
```

Terminal 2 — Frontend:
```bash
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** (Vite dev server proxies `/api` to the backend).

### REST API

| Endpoint | Form Fields | Returns |
|---|---|---|
| `POST /api/rotate` | `file`, `pages` (e.g. `"1,2,3"`), `angle` (default 180) | PDF |
| `POST /api/merge` | `file1`, `file2` | PDF |
| `POST /api/order` | `file`, `num_pages`, `new_order` (e.g. `"1,3,2"`) | PDF |
| `POST /api/convert` | `file`, `rtl` (`auto`\|`on`\|`off`, default `auto`) | DOCX |
| `POST /api/docx2pdf` | `file` | PDF |
| `POST /api/sanitize` | `file`, `mode` (`ocr`\|`basic`\|`ats`, default `ocr`), `lang` (default `eng+heb`) | PDF |

```bash
curl -X POST http://localhost:8000/api/rotate \
  -F "file=@input.pdf" -F "pages=1,2" -F "angle=90" \
  --output rotated.pdf
```

## Testing

**Backend (Python):**
```bash
uv run pytest
uv run pytest -v
uv run pytest --cov=pdf_editor --cov-report=term-missing
```

**Frontend (Node.js required):**
```bash
cd frontend && npm test
cd frontend && npm run test:coverage
```

## Notes

- Page numbers are **1-based** throughout (CLI and API)
- Rotation is always **clockwise**
- All operations are **non-destructive** — originals are never modified
- PDF→DOCX conversion may lose formatting on complex PDFs; scanned/image PDFs are not supported
- **Right-to-left PDFs**: verified by rendering the repaired DOCX back to PDF through
  LibreOffice and comparing against the source — bidi ordering matched the original on
  14 of 14 comparable lines, against 10 of 14 with the repair off, and paragraph positions
  were preserved. Not yet confirmed against Microsoft Word's renderer. Use `--rtl off` for
  the previous behaviour.
- MuPDF extracts characters in content-stream order, so Hebrew and
  Arabic lines come out with punctuation and digits on the wrong side (`נושא המחקר:` becomes
  `:נושא המחקר`), and pdf2docx emits no bidi markup at all. `convert` detects RTL script and
  repairs both — rebuilding logical word order from character positions and marking
  paragraphs, runs, and sections right-to-left. Left-to-right documents are untouched.
  Override detection with `--rtl on|off`.
- **DOCX→PDF** shells out to LibreOffice in headless mode. Each conversion gets a private
  user-profile directory so concurrent requests do not contend for a shared one.
- **Sanitize** renders each page to a 300 DPI image with PyMuPDF, OCRs it with Tesseract
  into a one-page PDF (image plus invisible text layer), and reassembles the pages with pypdf
  with every metadata field blanked. Hidden text, fonts, annotations and attachments do not
  survive. The text stays searchable and selectable but is no longer editable.
  `--mode basic` skips rasterizing: it uses PyMuPDF to remove metadata (info and XMP),
  annotations, form fields, JavaScript, attachments, links and thumbnails, then rewrites the
  file with garbage collection. It also removes hidden text: invisible or transparent text, text
  in a hidden layer, and text clipped away, which is how PDF editors "delete" a region while
  leaving its text in the file. A MuPDF device records which glyphs land inside the active clip,
  and a content-stream filter drops the rest. It needs no Tesseract and keeps the original text,
  but text that is drawn yet obscured (white text, text under images) survives.
  `--mode ats` does what basic does, then redraws each page's visible text as vector outlines
  under an invisible text layer holding exactly that text, one line at a time in reading order.
  Copy-paste and ATS parsers that read in drawing order (PDFBox/Tika, pdfminer, pypdf) then get
  the page top to bottom. Blocks are ordered by XY-cut, so columns of running text are read one
  after the other while dates beside titles, or labels beside values, are read row by row. The
  layer uses an embedded blank font, as OCR'd PDFs do; right-to-left lines are stored in logical
  order. The page looks the same, but its text can no longer be edited, so edit the source
  document and run it again. Known limits: in right-to-left table rows (a label cell beside a
  value cell) extractors may join the cells in a different order than in the original, and
  Hebrew or Arabic with vowel marks can come out split into fragments. `ats_pdf` warns when a
  page's rebuilt text does not match its visible text.
