# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Editor is a dual-mode application for manipulating PDF files:
- **CLI Mode**: Command-line tool with four operations (rotate, merge, reorder, convert)
- **Web Mode**: Browser-based UI with REST API backend (FastAPI) and React frontend

Supported operations: rotate pages by 90/180/270°, merge PDFs, reorder pages, convert PDFs to DOCX.

## Architecture

The project uses a layered architecture supporting both CLI and web modes:

**Backend (Shared Core)**
- **Operations Layer** (`src/pdf_editor/pdf_operations.py`): Core PDF manipulation using `pypdf` (PDF ops), `pdf2docx` (conversion), and `PyMuPDF`/fitz (fallback text extraction)

**CLI Mode**
- **CLI Layer** (`src/pdf_editor/cli.py`): Argument parsing with `argparse`, four subcommands
- **Entry Point** (`src/pdf_editor/__main__.py`): Routes `serve` subcommand to web server, else to CLI

**Web Mode**
- **API Layer** (`src/pdf_editor/api/app.py`): FastAPI application factory, CORS middleware, static file serving
- **Routes** (`src/pdf_editor/api/routes.py`): Four POST endpoints (`/api/rotate`, `/api/merge`, `/api/order`, `/api/convert`) that wrap `pdf_operations` functions
- **Server** (`src/pdf_editor/_serve.py`): Thin uvicorn launcher
- **Frontend** (`frontend/`): React + Vite + TypeScript + Tailwind CSS

Key design points:
- Page numbers are 1-based (user-facing), converted to 0-based internally with pypdf
- All operations are non-destructive (create new output files)
- PDF operations never modified; API routes wrap them with file I/O and error translation
- Web routes use temporary directories with cleanup via FastAPI BackgroundTasks (cleanup after response sent)
- CORS configured for dev (localhost:5173 Vite); production serves React from same origin
- Dual-mode maintained via conditional in `__main__.py` — no architectural coupling

## Common Development Tasks

### Installing for Development

```bash
# Using uv (preferred, updates uv.lock)
uv pip install -e ".[web,dev]"

# Or pip
pip install -e ".[web,dev]"
```

### Running the CLI

```bash
# Rotate PDF (pages then -o output)
uv run python -m pdf_editor rotate input.pdf 1,2 -o output.pdf --angle 90

# Merge PDFs
uv run python -m pdf_editor merge file1.pdf file2.pdf -o merged.pdf

# Reorder pages (num_pages and new_order are positional, output is -o)
uv run python -m pdf_editor order input.pdf 4 1,3,2,5,4,6 -o reordered.pdf

# Convert to DOCX
uv run python -m pdf_editor convert input.pdf -o output.docx
```

All subcommands use `-o/--output` for the output path (default filenames: `rotated.pdf`, `merged.pdf`, `reordered.pdf`, `converted.docx`).

### Running the Web Server

```bash
# Start FastAPI server on http://localhost:8000
uv run python -m pdf_editor serve

# With auto-reload (development)
uv run uvicorn pdf_editor.api.app:app --reload --host 0.0.0.0 --port 8000
```

**Development workflow (hot reload for both frontend and backend):**

Terminal 1 — Backend:
```bash
uv run uvicorn pdf_editor.api.app:app --reload
```

Terminal 2 — Frontend (requires Node.js):
```bash
cd frontend && npm install && npm run dev
# Open http://localhost:5173 (Vite dev server proxies /api to localhost:8000)
```

### Running Tests

**Backend (Python):**
```bash
# All tests (operations + API + CLI integration)
uv run pytest

# Verbose output
uv run pytest -v

# With coverage
uv run pytest --cov=pdf_editor --cov-report=term-missing

# Specific file or test
uv run pytest tests/test_pdf_operations.py
uv run pytest tests/test_api.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_pdf_operations.py::TestPDFOperations::test_rotate_pdf_pages_single_page
```

**Frontend (Node.js required):**
```bash
cd frontend
npm install       # first time only
npm test          # vitest run (single pass)
npm run test:watch      # watch mode
npm run test:coverage   # with coverage
```

Frontend tests use Vitest + React Testing Library. Config: `frontend/vitest.config.ts`. Setup: `frontend/src/test/setup.ts`.

### Building and Running via Docker

```bash
# Build and run with docker-compose (recommended)
docker-compose up --build
# Open http://localhost:8000

# Or build and run manually
docker build -t pdf-editor .
docker run -p 8000:8000 -e FRONTEND_DIST=/app/frontend/dist pdf-editor
```

Key Dockerfile requirements (learned from debugging):
- `src/` must be copied **before** `uv pip install` (editable install needs sources present)
- Use `npm install` not `npm ci` (no `package-lock.json` in repo)
- `README.md` must be copied alongside `pyproject.toml` (hatchling requires it)
- Use editable install (`-e`) so `__file__`-relative path resolution works at runtime

### Frontend Build

```bash
# Development
cd frontend && npm run dev

# Production build
cd frontend && npm run build
# Output in frontend/dist (automatically included in Docker image)

# Preview built version
cd frontend && npm run preview
```

## Key Files

**Backend Core**
- `src/pdf_editor/pdf_operations.py` — Core PDF manipulation logic; start here for adding operations or fixing PDF bugs
- `src/pdf_editor/cli.py` — CLI argument parsing with `argparse`; modify for new CLI subcommands
- `src/pdf_editor/__main__.py` — Entry point; routes `serve` subcommand to web, else to CLI

**Web Backend**
- `src/pdf_editor/api/app.py` — FastAPI application factory; includes CORS middleware and static file serving
- `src/pdf_editor/api/routes.py` — Four POST endpoints wrapping `pdf_operations`; all use temp files + BackgroundTasks cleanup
- `src/pdf_editor/_serve.py` — Uvicorn launcher for web mode

**Frontend (React)**
- `frontend/src/App.tsx` — Main app; tab navigation for four operations
- `frontend/src/hooks/useOperation.ts` — Shared hook for operation state (idle/loading/success/error) and file download
- `frontend/src/components/FileDropzone.tsx` — Drag-and-drop file input component
- `frontend/src/components/OperationResult.tsx` — Status/error/success display
- `frontend/src/operations/*.tsx` — Operation-specific forms (Rotate, Merge, Order, Convert)
- `frontend/vite.config.ts` — Vite config with `/api` proxy to localhost:8000
- `frontend/tailwind.config.js` — Tailwind CSS configuration

**Configuration & Deployment**
- `pyproject.toml` — Package metadata, dependencies, entry points; requires Python 3.13+
- `Dockerfile` — Multi-stage build: Node (React build) → Python (app + static files)
- `docker-compose.yml` — Local Docker Compose setup
- `.gitignore` — Includes `node_modules/`, `frontend/dist/`, `frontend/.vite/`

**Tests**
- `tests/test_pdf_operations.py` — Unit tests for all PDF operations; covers rotation metadata, order validation errors, DOCX validity
- `tests/test_api.py` — FastAPI endpoint tests; covers success responses, page counts, 422/500 error cases, content-disposition headers
- `tests/test_cli.py` — CLI integration tests via subprocess; covers all four subcommands end-to-end
- `frontend/src/test/` — Vitest + React Testing Library frontend tests (App, FileDropzone, OperationResult, useOperation hook)

## Testing Patterns

**CLI/PDF Operations Tests** (`tests/test_pdf_operations.py`)
- Use `TestPDFOperations` class with `create_test_pdf()` helper that generates blank PDFs
- Temporary files via `tempfile.NamedTemporaryFile` with automatic cleanup
- Import directly from `pdf_editor.pdf_operations` (not `src.pdf_editor`)
- Verify rotation via `page.rotation` in PDF metadata; verify DOCX output with `python-docx`

**API Tests** (`tests/test_api.py`)
- Use `TestClient` from `fastapi.testclient` (sync, no async needed)
- Helper function `make_pdf_bytes(pages=2)` creates test PDFs with `PdfWriter`
- Test multipart form data uploads and blob downloads; verify page counts via `PdfReader`
- Assert status codes: 200 (success), 422 (missing/invalid fields), 500 (operation errors)

**CLI Integration Tests** (`tests/test_cli.py`)
- Use `subprocess.run([sys.executable, '-m', 'pdf_editor', ...])` to exercise the full arg-parsing chain
- Helper `make_test_pdf()` creates temp PDFs; all temp files are cleaned up in `finally` blocks
- Verify returncode == 0 for success, != 0 for invalid args/operations

**Frontend Tests** (`frontend/src/test/`)
- Vitest + React Testing Library; run with `npm test` in the `frontend/` directory
- `URL.createObjectURL` and `revokeObjectURL` are stubbed in `setup.ts` (not in jsdom)
- `useOperation` tests mock `fetch` with `vi.stubGlobal` to simulate success/error responses
- Component tests use `@testing-library/user-event` for realistic user interactions

## Dependencies

**Core** (always required):
- `pypdf>=4.0.0` — PDF manipulation
- `pdf2docx>=0.5.0` — PDF to DOCX conversion
- `pymupdf>=1.24.0` — Fallback text extraction
- `python-docx>=1.1.0` — DOCX file handling

**Web** (optional, `[web]` group):
- `fastapi>=0.115.0` — Web framework
- `uvicorn[standard]>=0.32.0` — ASGI server
- `python-multipart>=0.0.12` — Multipart form parsing

**Dev** (optional, `[dev]` group):
- `pytest>=7.0.0`, `pytest-cov>=4.0.0` — Testing
- `httpx>=0.27.0` — HTTP client for TestClient

Install all: `uv pip install -e ".[web,dev]"`

## API Endpoints

All endpoints are POST, accept multipart/form-data, return binary file with cleanup via BackgroundTasks.

| Endpoint | Form Fields | Returns |
|---|---|---|
| `/api/rotate` | `file` (PDF), `pages` (str, e.g. "1,2,3"), `angle` (int, default 180) | PDF |
| `/api/merge` | `file1` (PDF), `file2` (PDF) | PDF |
| `/api/order` | `file` (PDF), `num_pages` (int), `new_order` (str, e.g. "1,3,2,5,4,6") | PDF |
| `/api/convert` | `file` (PDF) | DOCX |

Error handling: validation errors return 422; server errors return 500 with message.

## Important Notes

- Page numbers in CLI/API are 1-based; pypdf uses 0-based internally (conversion in `pdf_operations`)
- The `order_pdf_pages` function validates that reorder list is a permutation of 1 to num_pages
- PDF to DOCX conversion can fail silently on complex PDFs and fall back to text extraction (loses formatting/layout)
- Temp directory cleanup in web routes happens *after* FileResponse is sent (via BackgroundTasks) — critical for streaming
- All API routes wrap `pdf_operations` functions; never modify pdf_operations for API behavior changes
- Development CORS configured only for localhost:5173 (Vite dev server); production uses same-origin serving
- The project requires Python 3.13+ as specified in `pyproject.toml`
- Frontend requires Node.js 18+ for development (npm/npx)
- Dual-mode entry point in `__main__.py` checks for "serve" argument before routing to CLI
- `app.py` resolves `frontend/dist` via `FRONTEND_DIST` env var (set in docker-compose); falls back to `__file__`-relative path for local dev with editable install
