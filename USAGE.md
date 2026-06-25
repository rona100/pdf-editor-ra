# PDF Editor - Usage Guide

## Overview

PDF Editor is a dual-mode application for manipulating PDF files. Use it as a **command-line tool** for automation and scripting, or as a **web-based application** with a user-friendly graphical interface. Supported operations include:
- Rotate pages by 90, 180, or 270 degrees
- Merge multiple PDF files
- Reorder pages
- Convert PDFs to DOCX format

## Installation

### Prerequisites

- **Python 3.13+** (required for the project)
- **uv** (recommended package manager; [install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 18+** (only needed for web frontend development)

### Setup

Install the package with all dependencies:

```bash
# Using uv (preferred)
uv pip install -e ".[web,dev]"

# Or using pip
pip install -e ".[web,dev]"
```

The `web` extra installs FastAPI/Uvicorn; `dev` installs testing tools. For CLI-only use:
```bash
uv pip install -e .
```

## CLI Mode

### Basic Usage

Run operations from the command line with `uv run`:

```bash
uv run python -m pdf_editor <operation> [options]
```

### Operations

#### Rotate Pages

Rotate specific pages by 90, 180, or 270 degrees.

```bash
uv run python -m pdf_editor rotate <input_pdf> <pages> -o <output_pdf> [--angle ANGLE]
```

**Arguments:**
- **input_pdf**: Path to the input PDF
- **pages**: Comma-separated page numbers (1-based indexing, e.g., `1,2,5`)
- **-o, --output**: Path for the output PDF (default: `rotated.pdf`)
- **--angle, -a**: Rotation angle (90, 180, or 270; default: 180)

**Examples:**
```bash
# Rotate pages 1 and 2 by 180 degrees
uv run python -m pdf_editor rotate document.pdf 1,2 -o rotated.pdf

# Rotate pages 3, 5, 7 by 90 degrees clockwise
uv run python -m pdf_editor rotate document.pdf 3,5,7 --angle 90 -o output.pdf

# Rotate page 10 by 270 degrees
uv run python -m pdf_editor rotate document.pdf 10 -a 270
```

#### Merge PDFs

Combine two PDF files into one.

```bash
uv run python -m pdf_editor merge <file1> <file2> -o <output_pdf>
```

**Arguments:**
- **file1**: Path to the first PDF
- **file2**: Path to the second PDF
- **-o, --output**: Path for the merged PDF (default: `merged.pdf`)

**Examples:**
```bash
# Merge two documents
uv run python -m pdf_editor merge report.pdf appendix.pdf -o complete.pdf

# Combine chapters
uv run python -m pdf_editor merge chapter1.pdf chapter2.pdf -o book.pdf
```

#### Reorder Pages

Rearrange pages by specifying the new order.

```bash
uv run python -m pdf_editor order <input_pdf> <num_pages> <new_order> -o <output_pdf>
```

**Arguments:**
- **input_pdf**: Path to the input PDF
- **num_pages**: Number of pages to reorder from the start (integer)
- **new_order**: Comma-separated list showing which original page goes to each position (e.g., `1,3,2,5,4,6`)
- **-o, --output**: Path for the reordered PDF (default: `reordered.pdf`)

**Examples:**
```bash
# Custom reorder: position 1 gets page 1, position 2 gets page 3, etc.
uv run python -m pdf_editor order document.pdf 6 1,3,2,5,4,6 -o output.pdf

# Reverse the first 4 pages
uv run python -m pdf_editor order document.pdf 4 4,3,2,1 -o reversed.pdf
```

#### Convert to DOCX

Convert a PDF file to Microsoft Word format.

```bash
uv run python -m pdf_editor convert <input_pdf> -o <output_docx>
```

**Arguments:**
- **input_pdf**: Path to the input PDF
- **-o, --output**: Path for the output DOCX (default: `converted.docx`)

**Example:**
```bash
uv run python -m pdf_editor convert document.pdf -o output.docx
```

### Getting Help

```bash
uv run python -m pdf_editor --help
uv run python -m pdf_editor <operation> --help  # Help for a specific operation
```

---

## Web Mode

Access PDF Editor via a browser-based interface with a REST API backend.

### Quick Start

> **No Node.js?** Use Docker Compose instead — it builds the frontend automatically. See the [Docker Deployment](#docker-deployment) section below.

If you have already built the frontend (`frontend/dist/` exists), start the web server:

```bash
uv run python -m pdf_editor serve
```

The application will be available at **http://localhost:8000**

### Development with Hot Reload

For active development, run the backend and frontend separately with auto-reloading:

**Terminal 1 — Backend (FastAPI):**
```bash
uv run uvicorn pdf_editor.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend (React/Vite):**
```bash
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173** in your browser. The Vite dev server proxies `/api` requests to `localhost:8000`, and both frontend and backend reload automatically on file changes.

### Web Interface

The web app provides a tabbed interface:
- **Rotate**: Upload a PDF, select pages to rotate, choose rotation angle, download result
- **Merge**: Upload two PDFs and merge them
- **Reorder**: Upload a PDF, specify the number of pages and new order
- **Convert**: Upload a PDF and convert it to DOCX

All operations are non-destructive; original files are never modified.

### REST API Endpoints

If you prefer to automate web requests, all operations are available as POST endpoints:

| Endpoint | Fields | Returns |
|---|---|---|
| `POST /api/rotate` | `file` (PDF), `pages` (str: "1,2,3"), `angle` (int: 90/180/270) | PDF |
| `POST /api/merge` | `file1` (PDF), `file2` (PDF) | PDF |
| `POST /api/order` | `file` (PDF), `num_pages` (int), `new_order` (str: "1,3,2") | PDF |
| `POST /api/convert` | `file` (PDF) | DOCX |

**Example (using curl):**
```bash
curl -X POST http://localhost:8000/api/rotate \
  -F "file=@input.pdf" \
  -F "pages=1,2" \
  -F "angle=90" \
  --output rotated.pdf
```

---

## Docker Deployment

### Using Docker (Production)

Build and run the Docker image:

```bash
# Build the image
docker build -t pdf-editor .

# Run the container
docker run -p 8000:8000 pdf-editor
```

Open **http://localhost:8000** in your browser.

### Using Docker Compose (Local Development)

A `docker-compose.yml` file is included for easier local setup:

```bash
# Start the application
docker-compose up --build

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

This builds and runs both the backend and frontend in a single container, available at **http://localhost:8000**.

### Docker Image Details

The Dockerfile uses a multi-stage build:
1. **Stage 1 (Node)**: Builds the React frontend with Vite
2. **Stage 2 (Python)**: Copies the built frontend and runs the FastAPI backend

The final image is ~300MB and includes:
- Python 3.13 with all dependencies
- Built React frontend served by FastAPI
- Production-ready Uvicorn ASGI server

---

## Frontend Build (Manual)

If you want to build the frontend independently:

### Development Build
```bash
cd frontend
npm install
npm run dev
```

### Production Build
```bash
cd frontend
npm install
npm run build
```

The built files are output to `frontend/dist/` and are automatically included in the Docker image.

### Preview Production Build
```bash
cd frontend
npm run preview
```

---

## Testing

Run the test suite to verify functionality:

```bash
# All tests
uv run pytest

# Verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=pdf_editor --cov-report=term-missing

# Specific test file
uv run pytest tests/test_pdf_operations.py

# Specific test
uv run pytest tests/test_pdf_operations.py::TestPDFOperations::test_rotate_pdf_pages
```

---

## Tips & Important Notes

### General
- **Page numbers use 1-based indexing** (first page is 1, not 0)
- **Rotation is always clockwise** (90° = 1/4 turn clockwise)
- **Files are never modified in place**; output is always written to a new file
- **Original files must have read permission**; output directory must have write permission

### CLI Usage
- Separate multiple page numbers with commas (spaces optional: `1,2,3` or `1, 2, 3`)
- Use `uv run` to ensure dependencies are properly resolved
- For long commands, consider using aliases or shell scripts

### Web Mode
- All operations run on the server; large PDFs may take a few seconds
- Temporary files are automatically cleaned up after download
- For security, avoid exposing the API endpoint to untrusted networks without authentication
- CORS is configured for development (localhost:5173); production serves frontend from the same origin

### Conversion to DOCX
- PDF→DOCX conversion may lose formatting on complex PDFs (tables, special fonts, etc.)
- If conversion fails silently, the system falls back to text extraction (plain text only)
- Scanned PDFs (image-based) cannot be converted to DOCX; use OCR preprocessing if needed

---

## Troubleshooting

### "Command not found: pdf-editor"
Make sure you installed with `pip install -e .` and the package is available in your Python environment. Use `uv run python -m pdf_editor` instead.

### "ModuleNotFoundError: No module named 'pdf_editor'"
Install the package: `uv pip install -e ".[web,dev]"`

### Web server won't start on port 8000
- The port may be in use. Specify a different port: `uv run uvicorn pdf_editor.api.app:app --port 8001`
- Or kill the existing process: `lsof -ti:8000 | xargs kill -9` (macOS/Linux)

### PDF operations fail with "Permission denied"
Ensure input PDFs are readable and the output directory is writable:
```bash
chmod +r input.pdf
chmod +w output_directory/
```

### Docker build fails
Ensure you have Docker and sufficient disk space. Try:
```bash
docker system prune  # Clean up unused Docker resources
docker build --no-cache -t pdf-editor .
```

### http://localhost:8000 returns `{"detail": "Not Found"}`
The frontend hasn't been built. Use Docker Compose (`docker-compose up --build`) which builds the frontend automatically, or build manually with Node.js (`cd frontend && npm install && npm run build`) then restart the server.
