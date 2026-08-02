"""Right-to-left repair pass for a generated DOCX.

NOT WORKING YET: see the note in rtl.py -- Hebrew output still does not render
correctly in Word.

pdf2docx lays out tables, images and positioning faithfully but is entirely
bidi-unaware: it emits no ``<w:bidi>`` or ``<w:rtl>`` properties at all, so Word
re-runs its own bidi algorithm with a left-to-right base direction and renders
Hebrew or Arabic paragraphs backwards. This module patches the converted
document in place — substituting logical-order text from a correction table and
marking paragraphs, runs and sections as right-to-left.

Paragraph alignment is deliberately left alone: pdf2docx derives ``w:jc`` from
where the text actually sits on the page, and Word treats left/right as
physical rather than direction-relative, so its choice is already correct.
"""

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .rtl import has_rtl, normalize

# Child ordering required by the OOXML schema. Elements inserted out of order
# make Word reject the document, so a new child has to go before the first of
# its successors that is already present.
_PPR_SEQ = (
    "w:pStyle", "w:keepNext", "w:keepLines", "w:pageBreakBefore", "w:framePr",
    "w:widowControl", "w:numPr", "w:suppressLineNumbers", "w:pBdr", "w:shd",
    "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap",
    "w:overflowPunct", "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN",
    "w:bidi", "w:adjustRightInd", "w:snapToGrid", "w:spacing", "w:ind",
    "w:contextualSpacing", "w:mirrorIndents", "w:suppressOverlap", "w:jc",
    "w:textDirection", "w:textAlignment", "w:textboxTightWrap", "w:outlineLvl",
    "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)

_RPR_SEQ = (
    "w:rStyle", "w:rFonts", "w:b", "w:bCs", "w:i", "w:iCs", "w:caps",
    "w:smallCaps", "w:strike", "w:dstrike", "w:outline", "w:shadow",
    "w:emboss", "w:imprint", "w:noProof", "w:snapToGrid", "w:vanish",
    "w:webHidden", "w:color", "w:spacing", "w:w", "w:kern", "w:position",
    "w:sz", "w:szCs", "w:highlight", "w:u", "w:effect", "w:bdr", "w:shd",
    "w:fitText", "w:vertAlign", "w:rtl", "w:cs", "w:em", "w:lang",
    "w:eastAsianLayout", "w:specVanish", "w:oMath",
)

_SECTPR_SEQ = (
    "w:footnotePr", "w:endnotePr", "w:type", "w:pgSz", "w:pgMar", "w:paperSrc",
    "w:pgBorders", "w:lnNumType", "w:pgNumType", "w:cols", "w:formProt",
    "w:vAlign", "w:noEndnote", "w:titlePg", "w:textDirection", "w:bidi",
    "w:rtlGutter", "w:docGrid", "w:printerSettings", "w:sectPrChange",
)


def _ensure_child(parent, tag: str, sequence: tuple[str, ...]):
    """
    Returns `parent`'s `tag` child, creating it in schema order if absent.

    Args:
        parent: The oxml element to add to.
        tag (str): Qualified tag name, e.g. "w:rtl".
        sequence (tuple): The schema's child ordering for `parent`.
    """
    existing = parent.find(qn(tag))
    if existing is not None:
        return existing

    child = OxmlElement(tag)
    # insert_element_before() qualifies the successor names itself.
    parent.insert_element_before(child, *sequence[sequence.index(tag) + 1:])
    return child


def _repair_text(text_el, corrections: dict[str, str]) -> bool:
    """
    Replaces a <w:t>'s content with its logical-order form.

    Falls back to a whitespace-normalized lookup, and leaves the text untouched
    when nothing matches — a miss must never corrupt the document.

    Returns:
        bool: True if a correction was applied.
    """
    original = text_el.text
    if not original or not has_rtl(original):
        return False

    corrected = corrections.get(original)
    if corrected is None:
        loose = corrections.get(normalize(original))
        if loose is not None:
            # Matched on collapsed whitespace, so keep this run's own padding
            # rather than the padding the correction happened to carry.
            lead = original[:len(original) - len(original.lstrip())]
            trail = original[len(original.rstrip()):]
            corrected = lead + loose.strip() + trail
    if corrected is None or corrected == original:
        return False

    text_el.text = corrected
    return True


def _mark_run_rtl(run_el) -> None:
    """Adds complex-script properties so Word renders the run right-to-left."""
    rPr = run_el.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        run_el.insert(0, rPr)

    _ensure_child(rPr, "w:rtl", _RPR_SEQ)

    # Word applies size, weight and font to complex scripts through the "Cs"
    # variants, so mirror whatever pdf2docx set for the Latin ones.
    size = rPr.find(qn("w:sz"))
    if size is not None and size.get(qn("w:val")):
        _ensure_child(rPr, "w:szCs", _RPR_SEQ).set(qn("w:val"), size.get(qn("w:val")))

    for latin, complex_script in (("w:b", "w:bCs"), ("w:i", "w:iCs")):
        source = rPr.find(qn(latin))
        if source is None:
            continue
        target = _ensure_child(rPr, complex_script, _RPR_SEQ)
        val = source.get(qn("w:val"))
        if val is not None:
            target.set(qn("w:val"), val)
        elif target.get(qn("w:val")) is not None:
            del target.attrib[qn("w:val")]

    fonts = rPr.find(qn("w:rFonts"))
    if fonts is not None and fonts.get(qn("w:ascii")):
        fonts.set(qn("w:cs"), fonts.get(qn("w:ascii")))


def apply_rtl(docx_path: str, corrections: dict[str, str] | None = None) -> dict[str, int]:
    """
    Rewrites a DOCX in place so right-to-left content renders correctly.

    Args:
        docx_path (str): Path to the DOCX file to patch.
        corrections (dict): Optional mapping of mis-ordered extracted text to
            logical-order text, as built by `rtl.build_line_corrections`. When
            omitted, only direction properties are applied.

    Returns:
        dict: Counts of "paragraphs" marked RTL, "runs" marked RTL, plus
        "text_fixed" and "text_unmatched". Note that "text_unmatched" also
        counts runs that simply needed no correction, so it is an upper bound
        on the misses rather than an exact count.
    """
    corrections = corrections or {}
    stats = {"paragraphs": 0, "runs": 0, "text_fixed": 0, "text_unmatched": 0}

    document = Document(docx_path)
    body = document.element.body

    # iter() reaches paragraphs nested inside tables, which is where most of
    # the text in a converted form actually lives.
    for paragraph_el in body.iter(qn("w:p")):
        paragraph_is_rtl = False

        for run_el in paragraph_el.findall(qn("w:r")):
            run_is_rtl = False
            for text_el in run_el.findall(qn("w:t")):
                if not text_el.text or not has_rtl(text_el.text):
                    continue
                run_is_rtl = True
                if _repair_text(text_el, corrections):
                    stats["text_fixed"] += 1
                elif corrections:
                    stats["text_unmatched"] += 1

            if run_is_rtl:
                _mark_run_rtl(run_el)
                stats["runs"] += 1
                paragraph_is_rtl = True

        if paragraph_is_rtl:
            pPr = paragraph_el.find(qn("w:pPr"))
            if pPr is None:
                pPr = OxmlElement("w:pPr")
                paragraph_el.insert(0, pPr)
            _ensure_child(pPr, "w:bidi", _PPR_SEQ)
            stats["paragraphs"] += 1

    if stats["paragraphs"]:
        # sectPr sits either directly under body or inside a paragraph's pPr.
        for sectPr in body.iter(qn("w:sectPr")):
            _ensure_child(sectPr, "w:bidi", _SECTPR_SEQ)

    document.save(docx_path)
    return stats
