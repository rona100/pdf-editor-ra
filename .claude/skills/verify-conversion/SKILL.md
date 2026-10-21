---
name: verify-conversion
description: Visually verify PDF→DOCX conversion quality by round-tripping a PDF through DOCX and back via LibreOffice and comparing page renders side by side. Use after any change to pdf_operations.py, rtl.py or docx_rtl.py, when debugging RTL/Hebrew layout, missing text, shaded regions or text boxes, and before claiming a conversion fix works. Passing tests are not enough here: they have passed while the rendered output was wrong.
argument-hint: "[input.pdf ...] [--rtl auto|on|off]"
allowed-tools: Bash(.venv/bin/python .claude/skills/verify-conversion/render.py *), Bash(.venv/bin/python tests/fixtures/make_fixtures.py), Read
---

# Verify a PDF→DOCX conversion visually

## Inputs
- If the user names PDFs, use those.
- Otherwise use the synthetic fixtures in `tests/fixtures/`: `ltr.pdf`, `hebrew.pdf`, `mixed.pdf`, `shaded_table.pdf`, `textbox.pdf`. If any are missing, regenerate them with `.venv/bin/python tests/fixtures/make_fixtures.py`.
- Never pick up the personal PDFs in the repository root on your own initiative. Use them only when the user names one explicitly.

## Run
For each input, write the output into the session scratchpad, not the repository:

```
.venv/bin/python .claude/skills/verify-conversion/render.py <input.pdf> <scratchpad>/verify/<stem> [--rtl auto|on|off]
```

The script prints the page counts, the text coverage (the same metric `_warn_if_incomplete` uses, warning below 95%), whether the text-only fallback ran, and one side-by-side PNG per page: source on the left, round-trip on the right.

## Inspect
Read every PNG and check it against this list:
1. **Direction and alignment**: RTL paragraphs are right-aligned, and lines read right to left. Lines are not mirrored or reversed word by word.
2. **Mixed runs**: numbers, dates, emails and Latin words inside Hebrew keep their internal left-to-right order and sit in the right place.
3. **Spacing**: no words glued together. Lost spaces are a known RTL failure.
4. **Tables**: same number of columns and rows, with cells in the right column and column order mirrored correctly for RTL.
5. **Lost content**: shaded backgrounds, text boxes and framed regions are still present.
6. **Pagination**: the round-trip page count matches the source.

## Report
For each input give a one-line verdict (OK, or a list of problems) plus the coverage figure. Name the PNG path for anything you flag. A failed check means the change is not done. Fix it, or tell the user plainly what is still wrong.

The coverage number only measures words. Two cases mean the output is wrong even when the number looks fine: 100% coverage with glued words or scrambled columns, and a "fallback used: YES" line.
