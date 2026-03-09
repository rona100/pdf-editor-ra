# PDF Editor - Usage Guide

## Overview

This PDF Editor is a command-line tool that allows you to rotate specific pages in PDF files by 90, 180, or 270 degrees, and merge multiple PDF files into one.

## Requirements

- Python 3.x
- pypdf library

## Installation

Install the required dependencies:

```bash
pip install pypdf
```

Or if you have a `pyproject.toml` file:

```bash
pip install -e .
```

## Basic Usage

The tool uses subcommands to distinguish between different operations.

### Rotating Pages

**Command structure:**
```bash
python -m pdf_editor rotate <input_pdf> <output_pdf> <pages> [--angle ANGLE]
# or
pdf-editor rotate <input_pdf> <output_pdf> <pages> [--angle ANGLE]
```

### Arguments

- **input_pdf** (required): Path to the input PDF file
- **output_pdf** (required): Path where the rotated PDF will be saved
- **pages** (required): Comma-separated page numbers to rotate (1-based indexing)
- **--angle, -a** (optional): Rotation angle in degrees (90, 180, or 270; default is 180)

### Merging PDFs

**Command structure:**
```bash
python -m pdf_editor merge <file1> <file2> <output_pdf>
# or
pdf-editor merge <file1> <file2> <output_pdf>
```

### Arguments

- **file1** (required): Path to the first PDF file
- **file2** (required): Path to the second PDF file
- **output_pdf** (required): Path where the merged PDF will be saved

## Examples

### Example 1: Rotate pages 1 and 2 by 180 degrees

```bash
python -m pdf_editor rotate original.pdf rotated.pdf 1,2
pdf-editor rotate original.pdf rotated.pdf 1,2
```

### Example 2: Rotate pages 3, 5, and 7 by 90 degrees clockwise

```bash
python -m pdf_editor rotate original.pdf rotated.pdf 3,5,7 --angle 90
```

### Example 3: Rotate page 10 by 270 degrees clockwise

```bash
python -m pdf_editor rotate original.pdf rotated.pdf 10 -a 270
```

### Example 4: Merge two PDF files

```bash
python -m pdf_editor merge report.pdf appendix.pdf complete_report.pdf
pdf-editor merge report.pdf appendix.pdf complete_report.pdf
```

### Example 5: Combine multiple documents

```bash
python -m pdf_editor merge chapter1.pdf chapter2.pdf book.pdf
```

## Help

To see all available options:

```bash
python -m pdf_editor --help
pdf-editor --help
```

## Tips

- Page numbers use **1-based indexing** (first page is 1, not 0)
- Separate multiple page numbers with commas (no spaces required, but they're allowed)
- Rotation is always **clockwise**
- The original PDF is not modified; the rotated version is saved to the specified output path
- For merging, pages from the first file come first, followed by pages from the second file
- Make sure you have read permission for the input PDFs and write permission for the output directory

## Notes

- Rotation is always **clockwise**
- If a file with the same output path already exists, it will be overwritten
- Make sure you have read permission for the input PDFs and write permission for the output directory
