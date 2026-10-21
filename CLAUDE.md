# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Editor is a dual-mode application for manipulating PDF files:
- **CLI Mode**: Command-line tool with four operations (rotate, merge, reorder, convert)
- **Web Mode**: Browser-based UI with REST API backend (FastAPI) and React frontend

Supported operations: rotate pages by 90/180/270°, merge PDFs, reorder pages, convert PDFs to DOCX.

## Key design points

- Page numbers are 1-based (user-facing), converted to 0-based internally with pypdf
- All operations are non-destructive (create new output files)
- PDF operations never modified; API routes wrap them with file I/O and error translation
- Web routes use temporary directories with cleanup via FastAPI BackgroundTasks (cleanup after response sent)
- CORS configured for dev (localhost:5173 Vite); production serves React from same origin
- Dual-mode maintained via conditional in `__main__.py` — no architectural coupling

## Docker

Key Dockerfile requirements (learned from debugging):
- `src/` must be copied **before** `uv pip install` (editable install needs sources present)
- Use `npm install` not `npm ci` (no `package-lock.json` in repo)
- `README.md` must be copied alongside `pyproject.toml` (hatchling requires it)
- Use editable install (`-e`) so `__file__`-relative path resolution works at runtime

## Testing gotchas

- Import directly from `pdf_editor.pdf_operations` (not `src.pdf_editor`)
- `URL.createObjectURL` and `revokeObjectURL` are stubbed in `frontend/src/test/setup.ts` (not present in jsdom)

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
