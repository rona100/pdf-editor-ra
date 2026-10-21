"""
Round-trips a PDF through PDF -> DOCX -> PDF and renders both ends to PNG.

For each page this writes one side-by-side image, source on the left and
round-tripped on the right, so a reviewer can see layout, alignment and RTL
direction problems that text-level tests miss. It also prints the text
coverage figure the converter itself uses to warn about lost content.

Usage:
    .venv/bin/python .claude/skills/verify-conversion/render.py INPUT.pdf OUTDIR [--rtl auto|on|off] [--dpi 80]
"""

import argparse
import contextlib
import io
import sys
from pathlib import Path

import fitz

from pdf_editor import pdf_operations


def side_by_side(left: fitz.Pixmap, right: fitz.Pixmap) -> fitz.Pixmap:
    """Joins two page renders horizontally on a white canvas with a gutter."""
    gutter = 12
    width = left.width + gutter + right.width
    height = max(left.height, right.height)
    canvas = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, width, height), False)
    canvas.clear_with(255)
    left.set_origin(0, 0)
    right.set_origin(left.width + gutter, 0)
    canvas.copy(left, left.irect)
    canvas.copy(right, right.irect)
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--rtl", default="auto", choices=pdf_operations.RTL_MODES)
    parser.add_argument("--dpi", type=int, default=80)
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    docx = args.outdir / f"{args.input.stem}.docx"
    roundtrip = args.outdir / f"{args.input.stem}.roundtrip.pdf"

    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        pdf_operations.convert_pdf_to_docx(str(args.input), str(docx), rtl=args.rtl)
    converter_output = log.getvalue().strip()

    with contextlib.redirect_stdout(io.StringIO()):
        pdf_operations.convert_docx_to_pdf(str(docx), str(roundtrip))

    coverage = pdf_operations._text_coverage(str(args.input), str(docx))
    used_fallback = "fallback" in converter_output.lower()

    source = fitz.open(args.input)
    result = fitz.open(roundtrip)
    images = []
    for index in range(max(len(source), len(result))):
        blank = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10), False)
        blank.clear_with(255)
        left = source[index].get_pixmap(dpi=args.dpi) if index < len(source) else blank
        right = result[index].get_pixmap(dpi=args.dpi) if index < len(result) else blank
        path = args.outdir / f"{args.input.stem}.page{index + 1}.png"
        side_by_side(left, right).save(path)
        images.append(path)

    print(f"source pages:      {len(source)}")
    print(f"round-trip pages:  {len(result)}")
    print(f"text coverage:     {coverage:.1%} (warning threshold {pdf_operations._COVERAGE_THRESHOLD:.0%})")
    print(f"fallback used:     {'YES - layout was discarded' if used_fallback else 'no'}")
    print(f"docx:              {docx}")
    print("converter output:")
    for line in converter_output.splitlines():
        print(f"  {line}")
    print("side-by-side images (source left, round-trip right):")
    for path in images:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
