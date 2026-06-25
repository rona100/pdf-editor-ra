# PDF Editor

A dual-mode application for manipulating PDF files — run it from the **command line** or use the **browser-based web interface**.

Supported operations:
- **Rotate** specific pages by 90, 180, or 270 degrees
- **Merge** two PDF files into one
- **Reorder** pages using a position mapping
- **Convert** PDFs to Microsoft Word DOCX format

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
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended)
- Docker (for web mode without Node.js)
- Node.js 18+ (only for frontend development)

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

# Convert to DOCX
uv run python -m pdf_editor convert <input> -o <output>

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
| `POST /api/convert` | `file` | DOCX |

```bash
curl -X POST http://localhost:8000/api/rotate \
  -F "file=@input.pdf" -F "pages=1,2" -F "angle=90" \
  --output rotated.pdf
```

## Testing

```bash
uv run pytest
uv run pytest -v
uv run pytest --cov=pdf_editor --cov-report=term-missing
```

## Notes

- Page numbers are **1-based** throughout (CLI and API)
- Rotation is always **clockwise**
- All operations are **non-destructive** — originals are never modified
- PDF→DOCX conversion may lose formatting on complex PDFs; scanned/image PDFs are not supported
