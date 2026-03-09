# PDF Editor

A command-line tool for rotating pages in PDF files and merging multiple PDFs. Easily rotate specific pages by 90, 180, or 270 degrees clockwise, or combine multiple PDF files into one.

## Features

- **Rotate specific pages** in PDF files (90, 180, or 270 degrees clockwise)
- **Merge multiple PDF files** into a single document
- Easy-to-use command-line interface with subcommands
- Preserves original files (output saved to new files)

## Requirements

- Python 3.x
- pypdf library

## Installation

Clone or download this repository, then install dependencies:

```bash
pip install pypdf
```

Or using the project file:

```bash
pip install -e .
```

After installation, you can use the tool as a module or as a command:

```bash
# As a Python module
python -m pdf_editor --help

# As a command (after installation)
pdf-editor --help
```

## Usage

The tool uses subcommands to distinguish between different operations.

### Rotating Pages

**Command structure:**
```bash
python -m pdf_editor rotate <input_pdf> <output_pdf> <pages> [--angle ANGLE]
# or
pdf-editor rotate <input_pdf> <output_pdf> <pages> [--angle ANGLE]
```

**Arguments:**
- **input_pdf**: Path to the input PDF file (required)
- **output_pdf**: Path where the rotated PDF will be saved (required)
- **pages**: Comma-separated page numbers to rotate, using 1-based indexing (required)
  - Examples: `1`, `1,2`, `1,3,5,7`
- **--angle, -a**: Rotation angle in degrees (90, 180, or 270; default is 180)

**Examples:**

**Rotate first and second pages by 180 degrees:**
```bash
python -m pdf_editor rotate original.pdf rotated.pdf 1,2
pdf-editor rotate original.pdf rotated.pdf 1,2
```

**Rotate pages 3, 5, and 7 by 90 degrees clockwise:**
```bash
python -m pdf_editor rotate original.pdf rotated.pdf 3,5,7 --angle 90
```

**Rotate page 10 by 270 degrees:**
```bash
python -m pdf_editor rotate original.pdf rotated.pdf 10 -a 270
```

### Merging PDFs

**Command structure:**
```bash
python -m pdf_editor merge <file1> <file2> <output_pdf>
# or
pdf-editor merge <file1> <file2> <output_pdf>
```

**Arguments:**
- **file1**: Path to the first PDF file (required)
- **file2**: Path to the second PDF file (required)
- **output_pdf**: Path where the merged PDF will be saved (required)

**Examples:**

**Merge two PDF files:**
```bash
python -m pdf_editor merge report.pdf appendix.pdf complete_report.pdf
pdf-editor merge report.pdf appendix.pdf complete_report.pdf
```

**Combine multiple documents:**
```bash
python -m pdf_editor merge chapter1.pdf chapter2.pdf book.pdf
```

### Getting Help

**General help:**
```bash
python -m pdf_editor --help
pdf-editor --help
```

**Help for rotate command:**
```bash
python -m pdf_editor rotate --help
```

**Help for merge command:**
```bash
python -m pdf_editor merge --help
```

## Important Notes

- **Page numbers use 1-based indexing** (the first page is 1, not 0)
- **Rotation is always clockwise**
- **Merging preserves page order** - pages from the first file come first, followed by pages from the second file
- **Original PDF files are never modified** - all operations create new output files
- **If output file exists, it will be overwritten**
- **Ensure you have read permissions** for input PDFs and **write permissions** for the output directory

## Example Workflows

### Rotating Pages
```bash
# Fix upside-down pages in a scanned document
python -m pdf_editor rotate scanned.pdf fixed.pdf 1,3,5

# Rotate landscape pages to portrait
python -m pdf_editor rotate document.pdf adjusted.pdf 2,4,6 --angle 90
```

### Merging PDFs
```bash
# Combine a report with its appendix
python -m pdf_editor merge report_main.pdf report_appendix.pdf final_report.pdf

# Create a complete book from chapters
python -m pdf_editor merge intro.pdf chapter1.pdf chapter2.pdf conclusion.pdf complete_book.pdf
```

## Troubleshooting

**"Error: Pages must be comma-separated integers"**
- Make sure page numbers are separated by commas with no spaces (or spaces are fine)
- Example correct format: `1,2,3` or `1, 2, 3`

**"No such file or directory"**
- Verify all input PDF file paths exist
- Ensure you have write permissions in the output directory

**Import Error for pypdf**
- Install pypdf using: `pip install pypdf`

**"unrecognized arguments"**
- Make sure you're using the correct subcommand (`rotate` or `merge`)
- Use `python -m pdf_editor --help` to see available commands

## Development

### Running Tests

This project includes comprehensive tests for both rotation and merging functionality.

```bash
# Run all tests with pytest
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage report
pytest --cov=pdf_editor --cov-report=term-missing

# Run specific test file
pytest test_pdf_operations.py

# Run simple test script (no pytest required)
python test_simple.py
```

### Test Coverage

The test suite covers:
- Single page rotation
- Multiple page rotation
- Invalid page number handling
- PDF merging with different page counts
- Different rotation angles (90°, 180°, 270°)
