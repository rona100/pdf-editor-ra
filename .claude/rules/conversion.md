---
paths:
  - "src/pdf_editor/pdf_operations.py"
  - "src/pdf_editor/rtl.py"
  - "src/pdf_editor/docx_rtl.py"
  - "tests/test_rtl.py"
  - "tests/test_docx_rtl.py"
  - "tests/fixtures/**"
---

# PDF→DOCX conversion and RTL repair

- pdf2docx skips a page whose layout it cannot build and still reports success, so a conversion that "worked" can be missing a page's content. `_convert_with_pdf2docx` passes `ignore_page_error=False` to turn that into an exception. It retries once with a relaxed `min_border_clearance`, and only then falls back to text extraction, which keeps all the text and none of the layout.
- pdf2docx can also drop content *without* raising. Shaded regions and text boxes are the usual casualties. `_warn_if_incomplete` compares the converted text against the PDF's lines and warns below 95% (`_COVERAGE_THRESHOLD`).
- RTL repair is gated on detection (`pdf_has_rtl`), so LTR documents produce byte-identical output to before the feature existed. `test_ltr_output_is_identical_with_rtl_off` enforces this. Keep it passing.
- RTL text substitution matches against exact and whitespace-normalized keys only. Unmatched runs are left untouched rather than guessed at.
- `_repair_rtl` swallows its own exceptions on purpose: a converted document with unrepaired RTL beats losing the conversion.
- DOCX→PDF passes `-env:UserInstallation` per call. Without it, concurrent LibreOffice invocations contend for one profile and hang.
- Passing tests do not prove a conversion change works. Run `/verify-conversion` and look at the renders before calling it done.
- Test with the synthetic PDFs in `tests/fixtures/` (regenerate them with `tests/fixtures/make_fixtures.py`), never with the personal PDFs in the repository root.
