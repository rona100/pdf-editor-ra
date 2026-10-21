# Hebrew table on a shaded background is mangled in PDF→DOCX

**Status:** open, not investigated beyond the findings below
**Found:** 2026-10-21, first run of the `/verify-conversion` skill
**Fixture:** `tests/fixtures/shaded_table.pdf` (synthetic, made by `tests/fixtures/make_fixtures.py`)

## Input

A Hebrew caption, "טבלה על רקע צבעוני:", above a borderless 3-column RTL table on a light-blue shaded band:

| פריט | כמות | מחיר |
|---|---|---|
| עט | 3 | 12.00 |
| מחברת | 5 | 45.50 |

## What goes wrong (DOCX rendered back to PDF through LibreOffice)

- **Spaces between words are lost.** The caption comes out as "טבלהעלרקעצבעוני:", and the cells "עט", "3", "מחברת" and "5" run together as "עט3מחברת5".
- **The table falls apart.** The "מחיר" header moves up onto the caption's line, the prices 12.00 and 45.50 sit next to the caption instead of in their rows, and the columns don't line up.
- **Text coverage is 75%**, below the 95% threshold, so `_warn_if_incomplete` does warn. This is not a silent loss.
- **The shaded background survives.** Shading is what pdf2docx was expected to drop; the text is the real problem.

Converter log:
```
Applied RTL repair: 4 paragraphs, 9 runs, 0 text fixes (9 unmatched)
Warning: about 25% of the PDF's text lines are missing from the converted document. ...
```

## What we know about the cause

- **Established:** the RTL text-fix step matched no runs (0 fixes, 9 unmatched), so by design it left the text alone. The damage happens earlier, in pdf2docx's layout and table step.
- **Hypothesis, not yet checked:** with no drawn borders, pdf2docx has to work out the table from where the text sits on the page. It gets that wrong for right-to-left text, and the word spacing is lost at the same point.

## Suggested first steps when picking this up

1. Reproduce: `.venv/bin/python .claude/skills/verify-conversion/render.py tests/fixtures/shaded_table.pdf /tmp/vc`, then look at `/tmp/vc/shaded_table.page1.png`.
2. Isolate the stage: convert with `rtl='off'` and inspect the raw pdf2docx output. If it is already glued and scrambled, the RTL repair is not involved.
3. Test the hypothesis: add a variant fixture with drawn table borders, and one with no shading, to see which change makes it convert correctly.
4. Once fixed, add a regression test (for example, that the converted text keeps the caption's word boundaries) and confirm visually with `/verify-conversion`.

## Why it matters

Tables on shaded backgrounds are common in real Hebrew documents such as pay slips and forms, so this is probably not limited to the test file.
