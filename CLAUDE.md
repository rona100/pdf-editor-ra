# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Editor is a command-line tool for manipulating PDF files. It provides four main operations: rotating specific pages by 90/180/270 degrees, merging multiple PDFs, reordering pages, and converting PDFs to Word DOCX format.

## Architecture

The project follows a clean layered architecture:

- **CLI Layer** (`src/pdf_editor/cli.py`): Command-line argument parsing using `argparse` with four subcommands (`rotate`, `merge`, `order`, `convert`)
- **Operations Layer** (`src/pdf_editor/pdf_operations.py`): Core PDF operations using `pypdf` for PDF manipulation, `pdf2docx` for conversion, and `PyMuPDF` (fitz) for fallback text extraction
- **Entry Point** (`src/pdf_editor/__main__.py`): Module execution entry point

Key design points:
- Page numbers are 1-based (user-facing), converted to 0-based internally when using pypdf
- All operations are non-destructive (create new output files, never modify inputs)
- PDF to DOCX conversion has a fallback text-extraction method if the standard `pdf2docx` converter fails
- Each operation prints a success message to stdout

## Common Development Tasks

### Running the CLI

```bash
# Using module interface
python -m pdf_editor [command] [args]

# Using installed command (after `pip install -e .`)
pdf-editor [command] [args]
```

### Running Tests

```bash
# All tests with pytest
pytest

# Tests with verbose output
pytest -v

# Tests with coverage report
pytest --cov=pdf_editor --cov-report=term-missing

# Single test file
pytest tests/test_pdf_operations.py

# Single test function
pytest tests/test_pdf_operations.py::TestPDFOperations::test_rotate_pdf_pages_single_page
```

### Installing for Development

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or using uv (project uses uv.lock)
uv pip install -e ".[dev]"
```

## Key Files

- `src/pdf_editor/pdf_operations.py` — Core PDF manipulation logic; start here for adding new operations or fixing PDF-related bugs
- `src/pdf_editor/cli.py` — Command routing and argument parsing; modify for new subcommands or CLI argument changes
- `tests/test_pdf_operations.py` — Test suite with fixtures for creating test PDFs; add tests here for new features
- `pyproject.toml` — Package metadata, dependencies, and scripts; requires Python 3.13+

## Testing Patterns

Tests use `TestPDFOperations` class with a helper method `create_test_pdf()` that generates blank test PDFs. The test suite uses temporary files (via `tempfile`) and cleans them up after assertions. All tests import directly from `pdf_editor.pdf_operations` (note: not `src.pdf_editor`).

## Important Notes

- Page numbers in CLI and function arguments are 1-based, but pypdf uses 0-based indexing internally
- The `order_pdf_pages` function validates that the reorder list is a permutation of 1 to num_pages
- PDF to DOCX conversion can fail silently on complex PDFs and fall back to text extraction (losing formatting and layout)
- The project requires Python 3.13+ as specified in `pyproject.toml`
