# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Editor is a dual-mode application for manipulating PDF files:
- **CLI Mode**: Command-line tool with five operations (rotate, merge, reorder, convert, docx2pdf)
- **Web Mode**: Browser-based UI with REST API backend (FastAPI) and React frontend

Supported operations: rotate pages by 90/180/270°, merge PDFs, reorder pages, convert PDFs to DOCX (with right-to-left repair), convert DOCX to PDF.

Topic-specific notes live in `.claude/rules/` and load when the matching files are touched: `conversion.md` (pdf2docx and RTL), `api.md`, `frontend.md` and `docker.md` (Docker and CI).

## Commands

```bash
.venv/bin/pytest -q                       # backend tests (~30s; CI uses `uv run --no-sync pytest`)
.venv/bin/pytest -q tests/test_rtl.py     # one file
ruff check src tests                      # lint (the code is not ruff-formatted; don't run `ruff format`)
npm --prefix frontend test                # frontend tests (vitest)
npx --prefix frontend tsc --noEmit -p frontend
python -m pdf_editor serve                # web app on :8000
npm --prefix frontend run dev             # Vite dev server on :5173, proxies /api
.venv/bin/python tests/fixtures/make_fixtures.py   # regenerate synthetic test PDFs
```

Use `/verify-conversion` to check PDF→DOCX output visually. Use the `rtl-reviewer` agent to review changes to conversion or RTL code.

## Key design points

- Page numbers are 1-based in the CLI and API. They are converted to 0-based for pypdf inside `pdf_operations`.
- All operations are non-destructive and write new output files.
- `order_pdf_pages` validates that the new order is a permutation of 1..num_pages.
- API routes wrap `pdf_operations` functions. Never change `pdf_operations` to get a different API behavior.
- Dual mode is a conditional in `__main__.py` (`serve` → web, otherwise CLI), with no architectural coupling between the two.
- Python 3.13+, Node 18+.

## System dependencies

- LibreOffice (`libreoffice-writer`) is optional and only needed for DOCX→PDF. It is located via `shutil.which('soffice'/'libreoffice')` or the `SOFFICE_BIN` env var.

## Testing gotchas

- Import from `pdf_editor.pdf_operations`, not `src.pdf_editor`.
- The PDFs and DOCX files in the repository root are the user's personal documents (gitignored). Don't read them or use them as test input unless asked. Use `tests/fixtures/` instead.
- A Stop hook runs the backend suite whenever Python files differ from HEAD. A PostToolUse hook runs `ruff check --fix` on each edited `.py` file and `tsc` after each `.ts`/`.tsx` edit.
