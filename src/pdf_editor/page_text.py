"""
Page-level text surgery on PDFs, built on MuPDF's device and content-filter APIs.

Two jobs live here:

- `remove_hidden_text` deletes characters that are drawn but cannot be seen:
  invisible or transparent text, text in a hidden layer, and text clipped
  away, which is how PDF editors "delete" a region without removing it.
- `rebuild_text_layer` redraws a page's visible text as vector outlines and
  lays an invisible text layer over it in reading order, so text extraction
  (copy-paste, ATS parsers) reads the page the way a person does.

PyMuPDF has no public API for content-stream filtering, so this module uses
the private helpers its own `scrub()` relies on (`_make_PdfFilterOptions`,
`_as_pdf_document`, `_as_pdf_page`). The tests exercise both paths, so a
PyMuPDF upgrade that changes them fails loudly.
"""

import ctypes
import re
import struct
import unicodedata

import fitz  # PyMuPDF
import pymupdf
from pymupdf import mupdf

from .rtl import has_rtl, is_rtl_char, logical_order


class _ClipTrackingDevice(mupdf.FzDevice2):
    """
    A MuPDF device that tracks the active clip and hands every text call to
    `_text`. Clips are tracked as bounding rectangles, so a glyph inside a
    clip's bounds but outside its exact shape counts as inside.
    """

    def __init__(self, page_area):
        super().__init__()
        for name in (
            'fill_text', 'stroke_text', 'clip_text', 'clip_stroke_text', 'ignore_text',
            'clip_path', 'clip_stroke_path', 'clip_image_mask', 'begin_mask', 'pop_clip',
        ):
            getattr(self, f'use_virtual_{name}')()
        self.clips = [page_area]

    def _text(self, text, ctm, kind: str, colorspace=None, color=None, alpha: float = 0.0, stroke=None) -> None:
        raise NotImplementedError

    def _glyphs(self, text, ctm):
        """Yields (font, gid, ucs, trm, bbox) for each glyph of a text object."""
        ctm = mupdf.FzMatrix(ctm)
        span = text.head
        while span:
            wrapped = mupdf.FzTextSpan(span)
            matrix = wrapped.trm()
            for i in range(wrapped.m_internal.len):
                item = wrapped.items(i)
                if item.gid < 0:
                    continue  # the rest of a multi-character glyph
                trm = mupdf.fz_concat(
                    mupdf.FzMatrix(matrix.a, matrix.b, matrix.c, matrix.d, item.x, item.y), ctm
                )
                yield wrapped.font(), item.gid, item.ucs, trm, mupdf.fz_bound_glyph(wrapped.font(), item.gid, trm)
            span = span.next

    def _in_clip(self, box, trm) -> bool:
        clip = self.clips[-1]
        if mupdf.fz_is_empty_rect(box):
            # A space has no ink, so judge it by where it sits.
            return clip.x0 <= trm.e <= clip.x1 and clip.y0 <= trm.f <= clip.y1
        return not mupdf.fz_is_empty_rect(mupdf.fz_intersect_rect(box, clip))

    def _push_clip(self, rect) -> None:
        self.clips.append(mupdf.fz_intersect_rect(self.clips[-1], mupdf.FzRect(rect)))

    def fill_text(self, ctx, text, ctm, colorspace, color, alpha, color_params):
        self._text(text, ctm, 'fill', colorspace, color, alpha)

    def stroke_text(self, ctx, text, stroke, ctm, colorspace, color, alpha, color_params):
        self._text(text, ctm, 'stroke', colorspace, color, alpha, stroke)

    def ignore_text(self, ctx, text, ctm):
        self._text(text, ctm, 'ignore')

    # The ll_ functions take MuPDF's borrowed pointers without wrapping them
    # in owning Python objects, which would free them a second time.
    def clip_text(self, ctx, text, ctm, scissor):
        self._text(text, ctm, 'clip')
        self._push_clip(mupdf.ll_fz_bound_text(text, None, ctm))

    def clip_stroke_text(self, ctx, text, stroke, ctm, scissor):
        self._text(text, ctm, 'clip')
        self._push_clip(mupdf.ll_fz_bound_text(text, stroke, ctm))

    def clip_path(self, ctx, path, even_odd, ctm, scissor):
        self._push_clip(mupdf.ll_fz_bound_path(path, None, ctm))

    def clip_stroke_path(self, ctx, path, stroke, ctm, scissor):
        self._push_clip(mupdf.ll_fz_bound_path(path, stroke, ctm))

    def clip_image_mask(self, ctx, image, ctm, scissor):
        self._push_clip(mupdf.fz_transform_rect(mupdf.FzRect(0, 0, 1, 1), mupdf.FzMatrix(ctm)))

    def begin_mask(self, ctx, area, luminosity, colorspace, color, color_params):
        self._push_clip(area)

    def pop_clip(self, ctx):
        if len(self.clips) > 1:
            self.clips.pop()


class _GlyphVisibility(_ClipTrackingDevice):
    """Lists every glyph drawn, in order, with whether it can be seen."""

    def __init__(self, page_area):
        super().__init__(page_area)
        self.glyphs = []  # (text, x, y, visible)
        self._last = None  # (text object, glyph count) and kind of the last call

    def _text(self, text, ctm, kind, colorspace=None, color=None, alpha=0.0, stroke=None):
        painted = kind in ('fill', 'stroke') and alpha > 0
        found = [
            (chr(ucs) if ucs > 0 else '', trm.e, trm.f, painted and self._in_clip(box, trm))
            for _, _, ucs, trm, box in self._glyphs(text, ctm)
        ]

        # Render modes that fill and stroke, or paint and clip, hand the same
        # text object to consecutive calls, but the content stream draws each
        # glyph once. Fold those calls together. Two fills are never folded:
        # identical text drawn twice is two sets of glyphs.
        key = (str(text), len(found))
        last = self._last
        self._last = (key, kind)
        if last and last[0] == key and (last[1], kind) in (('fill', 'stroke'), ('fill', 'clip'), ('stroke', 'clip')):
            start = len(self.glyphs) - len(found)
            for offset, (_, _, _, seen) in enumerate(found):
                drawn, x, y, before = self.glyphs[start + offset]
                self.glyphs[start + offset] = (drawn, x, y, before or seen)
            return
        self.glyphs.extend(found)


def remove_hidden_text(document, page) -> None:
    """
    Deletes every character on `page` that is drawn but cannot be seen.

    That covers invisible (render mode 3) and fully transparent text, text
    in a hidden optional-content layer, and text clipped away: outside a
    clipping path, a form XObject's BBox, or the page itself. Clipping is how
    editors "delete" a region without removing it, and copy-paste and ATS
    parsers still read such text.

    `_GlyphVisibility` runs the page and records, in drawing order, every
    glyph and whether it lands inside the clip in force. A content-stream
    filter then walks the same glyphs in the same order and removes the
    hidden ones. Text in a hidden layer is never run, so the device never
    reports it, and the filter removes it as unmatched.
    """
    device = _GlyphVisibility(mupdf.fz_bound_page(page.this))
    mupdf.fz_run_page_contents(page.this, device, mupdf.FzMatrix(), mupdf.FzCookie())
    glyphs = device.glyphs

    # The filter reports positions in PDF space; the device in page space.
    to_page = _page_matrix(page)
    position = [0]

    class HiddenTextFilter(mupdf.PdfSanitizeFilterOptions2):
        def __init__(self):
            super().__init__()
            self.use_virtual_text_filter()

        def text_filter(self, ctx, ucsbuf, ucslen, trm, ctm, bbox, *rest):
            origin = fitz.Point(0, 0) * fitz.Matrix(mupdf.FzMatrix(trm)) * fitz.Matrix(mupdf.FzMatrix(ctm)) * to_page
            text = _glyph_text(ucsbuf, ucslen)[:1]
            if position[0] < len(glyphs):
                drawn, x, y, visible = glyphs[position[0]]
                if drawn == text and abs(origin.x - x) < 0.01 and abs(origin.y - y) < 0.01:
                    position[0] += 1
                    return 0 if visible else 1
            return 1  # never drawn: a hidden optional-content layer

    _filter_text(document, page, HiddenTextFilter())

    # Every drawn glyph must have been matched; anything else means the two
    # walks disagreed, and the page cannot be trusted to be clean.
    if position[0] != len(glyphs):
        raise RuntimeError(
            f"Could not verify the text on page {page.number + 1}: "
            f"matched {position[0]} of {len(glyphs)} drawn characters"
        )


class _Outliner(_ClipTrackingDevice):
    """Collects the outline of every visible glyph, in PDF space."""

    def __init__(self, page_area, to_pdf):
        super().__init__(page_area)
        self.to_pdf = to_pdf
        self.shapes = []  # (paint operator, rgb, alpha, line width, clip or None, path operators)

    def _text(self, text, ctm, kind, colorspace=None, color=None, alpha=0.0, stroke=None):
        if kind not in ('fill', 'stroke') or alpha <= 0:
            return
        rgb = _rgb(colorspace, color)
        width = stroke.linewidth if stroke is not None else 0
        clip = self.clips[-1]
        for font, gid, _, trm, box in self._glyphs(text, ctm):
            if mupdf.fz_is_empty_rect(box) or not self._in_clip(box, trm):
                continue
            path = mupdf.fz_outline_glyph(font, gid, mupdf.fz_concat(trm, self.to_pdf))
            walker = _PathOperators()
            mupdf.fz_walk_path(path, walker, walker.m_internal)
            if not walker.ops:
                continue
            # Only a glyph the clip cuts through needs the clip redrawn.
            partial = None if mupdf.fz_contains_rect(clip, box) else mupdf.fz_transform_rect(clip, self.to_pdf)
            self.shapes.append(('f' if kind == 'fill' else 'S', rgb, alpha, width, partial, ' '.join(walker.ops)))


class _PathOperators(mupdf.FzPathWalker2):
    """Turns a MuPDF path into PDF path-construction operators."""

    def __init__(self):
        super().__init__()
        for name in ('moveto', 'lineto', 'curveto', 'closepath'):
            getattr(self, f'use_virtual_{name}')()
        self.ops = []

    def moveto(self, ctx, x, y):
        self.ops.append(f'{x:.3f} {y:.3f} m')

    def lineto(self, ctx, x, y):
        self.ops.append(f'{x:.3f} {y:.3f} l')

    def curveto(self, ctx, x1, y1, x2, y2, x3, y3):
        self.ops.append(f'{x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f} {x3:.3f} {y3:.3f} c')

    def closepath(self, ctx):
        self.ops.append('h')


def rebuild_text_layer(document, page, font_xref: int) -> None:
    """
    Replaces the page's text with outlines plus an invisible reading-order layer.

    Every visible glyph is redrawn as a filled (or stroked) vector outline in
    its own colour, so the page looks the same. All original text is then
    removed, and one invisible line of text per visible line is written in
    reading order with the glyphless font at `font_xref`. Text extraction
    sees only that layer.

    Run `remove_hidden_text` first: this reads the page's visible text, and
    MuPDF's extraction ignores clipping only for what it cannot see.
    """
    lines = _reading_order_lines(page)
    to_pdf = mupdf.fz_invert_matrix(_mupdf_page_matrix(page))

    outliner = _Outliner(mupdf.fz_bound_page(page.this), to_pdf)
    mupdf.fz_run_page_contents(page.this, outliner, mupdf.FzMatrix(), mupdf.FzCookie())

    class DropAllText(mupdf.PdfSanitizeFilterOptions2):
        def __init__(self):
            super().__init__()
            self.use_virtual_text_filter()

        def text_filter(self, *args):
            return 1

    _filter_text(document, page, DropAllText())

    # The filter empties text objects but keeps them (BT /F1 10 Tf ... ET),
    # and those still name the old fonts. Drop them and the font resources,
    # or a PDF editor looks for fonts that no longer draw anything.
    for xref in page.get_contents() + _page_forms(document, page.xref):
        stream = document.xref_stream(xref)
        if stream is not None:
            document.update_stream(xref, _TEXT_OBJECT.sub(b'', stream))
        if document.xref_get_key(xref, 'Resources/Font')[0] != 'null':
            document.xref_set_key(xref, 'Resources/Font', 'null')
    if document.xref_get_key(page.xref, 'Resources/Font')[0] != 'null':
        document.xref_set_key(page.xref, 'Resources/Font', 'null')

    page.wrap_contents()
    alphas = sorted({alpha for _, _, alpha, _, _, _ in outliner.shapes if alpha < 1})
    states = {alpha: f'GSa{i}' for i, alpha in enumerate(alphas)}
    content = _outline_operators(outliner.shapes, states) + '\n' + _text_layer_operators(lines, to_pdf)
    xref = document.get_new_xref()
    document.update_object(xref, '<<>>')
    document.update_stream(xref, content.encode())
    document.xref_set_key(
        page.xref, 'Contents', '[' + ' '.join(f'{x} 0 R' for x in page.get_contents() + [xref]) + ']'
    )
    document.xref_set_key(page.xref, 'Resources/Font', f'<</GLF0 {font_xref} 0 R>>')
    for alpha, name in states.items():
        document.xref_set_key(page.xref, f'Resources/ExtGState/{name}', f'<</ca {alpha:.4f}/CA {alpha:.4f}>>')


def _outline_operators(shapes, states: dict[float, str]) -> str:
    out = []
    for paint, (r, g, b), alpha, width, clip, path in shapes:
        out.append('q')
        if alpha < 1:
            out.append(f'/{states[alpha]} gs')
        if clip is not None:
            out.append(f'{clip.x0:.3f} {clip.y0:.3f} {clip.x1 - clip.x0:.3f} {clip.y1 - clip.y0:.3f} re W n')
        if paint == 'f':
            out.append(f'{r:.4f} {g:.4f} {b:.4f} rg {path} f')
        else:
            out.append(f'{r:.4f} {g:.4f} {b:.4f} RG {width:.3f} w {path} S')
        out.append('Q')
    return '\n'.join(out)


# Gaps narrower than this between blocks are not gutters between columns.
_MIN_GUTTER = 6
# Blocks whose tops are this close (in points) sit on the same row.
_ROW_TOLERANCE = 3


def _reading_order_lines(page) -> list[tuple[list[list[dict]], float, tuple[float, float], bool]]:
    """
    The page's visible lines in reading order, as text-layer entries of
    (pieces, font size, direction, right-to-left).

    Blocks are ordered by `_xy_cut`. Each line becomes clusters (a base
    character with its combining marks) measured along the line's own
    direction, split into pieces at wide gaps such as table cells. A
    left-to-right line becomes one entry per piece; a right-to-left line
    stays one entry, so its pieces are written in logical order together.
    """
    blocks = [b for b in page.get_text('rawdict')['blocks'] if b.get('lines')]
    page_text = ''.join(
        c['c'] for b in blocks for line in b['lines'] for s in line['spans'] for c in s['chars']
    )
    entries = []
    for block in _xy_cut(blocks, _mostly_rtl(page_text)):
        for line in block['lines']:
            chars = [c for span in line['spans'] for c in span['chars']]
            if not chars:
                continue
            size = line['spans'][0]['size']
            clusters = _clusters(chars, line['dir'])
            pieces = _split_at_gaps(clusters, size)
            if has_rtl(''.join(c['c'] for c in clusters)):
                entries.append((pieces, size, line['dir'], True))
            else:
                entries.extend(([piece], size, line['dir'], False) for piece in pieces)
    return entries


def _xy_cut(blocks: list[dict], rtl: bool) -> list[dict]:
    """
    Orders blocks for reading by recursive XY-cut.

    A vertical gutter splits the region into columns first, but only when
    the sides really are columns: side-by-side blocks that start on the same
    rows and hold single lines (dates beside job titles, labels beside
    values) are a table, read row by row. Otherwise the region is cut at its
    widest horizontal gap. Columns, and blocks side by side on a row, are
    read right to left on a mostly right-to-left page.
    """
    if len(blocks) <= 1:
        return list(blocks)

    columns = _partition(blocks, axis=0, min_gap=_MIN_GUTTER)
    if len(columns) > 1 and _are_columns(columns):
        return _read_side_by_side(columns, rtl)

    rows = _partition(blocks, axis=1, min_gap=0)
    if len(rows) > 1:
        # Cut only at the widest gap and recurse: cutting at every gap would
        # slice through columns wherever their paragraph breaks line up.
        widest = max(range(1, len(rows)), key=lambda i: _top(rows[i]) - _bottom(rows[i - 1]))
        above = [b for row in rows[:widest] for b in row]
        below = [b for row in rows[widest:] for b in row]
        return _xy_cut(above, rtl) + _xy_cut(below, rtl)

    if len(columns) > 1:
        return _read_side_by_side(columns, rtl)
    return sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))


def _read_side_by_side(groups: list[list[dict]], rtl: bool) -> list[dict]:
    ordered = list(reversed(groups)) if rtl else groups
    return [block for group in ordered for block in _xy_cut(group, rtl)]


def _partition(blocks: list[dict], axis: int, min_gap: float) -> list[list[dict]]:
    """Splits blocks into groups separated by empty bands along x (0) or y (1)."""
    ordered = sorted(blocks, key=lambda b: b['bbox'][axis])
    groups = [[ordered[0]]]
    reach = ordered[0]['bbox'][axis + 2]
    for block in ordered[1:]:
        if block['bbox'][axis] - reach > min_gap:
            groups.append([])
        groups[-1].append(block)
        reach = max(reach, block['bbox'][axis + 2])
    return groups


def _are_columns(groups: list[list[dict]]) -> bool:
    """
    Whether side-by-side groups are columns of running text rather than the
    cells of a table. Table cells start on shared rows and hold short text.
    """
    for left, right in zip(groups, groups[1:]):
        smaller, other = (left, right) if len(left) <= len(right) else (right, left)
        partnered = sum(
            any(abs(block['bbox'][1] - b['bbox'][1]) <= _ROW_TOLERANCE for b in other)
            for block in smaller
        )
        row_aligned = partnered >= len(smaller) / 2
        lines_per_block = min(
            sum(len(b['lines']) for b in group) / len(group) for group in (left, right)
        )
        if row_aligned and lines_per_block < 2:
            return False
    return True


def _top(blocks: list[dict]) -> float:
    return min(b['bbox'][1] for b in blocks)


def _bottom(blocks: list[dict]) -> float:
    return max(b['bbox'][3] for b in blocks)


def _mostly_rtl(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and sum(is_rtl_char(c) for c in letters) > len(letters) / 2


def _clusters(chars: list[dict], direction: tuple[float, float]) -> list[dict]:
    """
    Groups a line's characters into clusters, a base character followed by
    its combining marks (niqqud, harakat), measured along the line.

    A mark shares, or nearly shares, its base's position, so ranking marks
    by position on their own would scramble them against their bases.
    Each cluster records 'c' (its text), 'origin', 'start' and 'end' along
    the line's direction, 'index' (its place in the stored order), and
    'bbox' as (start, 0, end, 0) so `logical_order` can read positions along
    the line whatever its angle.
    """
    dx, dy = direction
    clusters = []
    for char in chars:
        text = char['c']
        if any(0xD800 <= ord(c) <= 0xDFFF for c in text):
            text = '�'  # a broken ToUnicode map yielded a lone surrogate
        start = char['origin'][0] * dx + char['origin'][1] * dy
        x0, y0, x1, y1 = char['bbox']
        end = max(start, x0 * dx + y0 * dy, x1 * dx + y1 * dy)
        if clusters and text and all(unicodedata.combining(c) for c in text):
            cluster = clusters[-1]
            cluster['c'] += text
            cluster['end'] = max(cluster['end'], end)
        else:
            clusters.append({'c': text, 'origin': char['origin'], 'start': start, 'end': end, 'index': len(clusters)})
    for cluster in clusters:
        cluster['bbox'] = (cluster['start'], 0, cluster['end'], 0)
    return clusters


def _split_at_gaps(clusters: list[dict], size: float) -> list[list[dict]]:
    """
    Splits a line, in visual order along its direction, where a gap wider
    than the font size separates clusters, as between the cells of a table
    row. Evenly spaced text-layer glyphs would otherwise close the gap.
    """
    visual = sorted(clusters, key=lambda c: c['start'])
    pieces = [[visual[0]]]
    for previous, cluster in zip(visual, visual[1:]):
        if cluster['start'] - previous['end'] > size:
            pieces.append([])
        pieces[-1].append(cluster)
    return pieces


# Every glyph of the glyphless font is this wide, in 1/1000 of the font size.
_GLYPH_WIDTH = 500


def _units(cluster: dict) -> int:
    """UTF-16 code units, which are the font's CIDs and its cells."""
    return len(cluster['c'].encode('utf-16-be')) // 2


def _text_layer_operators(entries, to_pdf) -> str:
    """
    Writes each entry as invisible text (render mode 3), stretched with Tz so
    every glyph fills an even cell: extractors then find word breaks only at
    real spaces.

    A left-to-right piece is one string from its start. A right-to-left
    line is one TJ in logical order, each cluster in the cell matching its
    visual rank within its piece and each piece at its original position:
    the way right-to-left PDFs store text, from which readers infer the
    direction. After each glyph the pen sits one cell past it, and a TJ
    adjustment moves it to the next cluster's cell.
    """
    matrix = fitz.Matrix(to_pdf.a, to_pdf.b, to_pdf.c, to_pdf.d, to_pdf.e, to_pdf.f)
    out = ['BT', '3 Tr']
    for pieces, size, (dx, dy), rtl in entries:
        size = size if size > 0 else 1
        natural = _GLYPH_WIDTH / 1000 * size

        def piece_cell(piece):
            width = max(c['end'] for c in piece) - piece[0]['start']
            return width / sum(_units(c) for c in piece) if width > 0 else natural

        # One cell width per text object: the narrowest piece's, so no piece
        # gets gaps between its glyphs.
        cell = min(piece_cell(piece) for piece in pieces)
        position = {}
        for piece in pieces:
            pen = piece[0]['start']
            for cluster in piece:
                position[id(cluster)] = pen
                pen += _units(cluster) * cell

        clusters = [c for piece in pieces for c in piece]
        if rtl:
            # logical_order orders runs but keeps each run's characters in
            # the order given, so start from the stored order, which is
            # logical within a run. It reads 'c' and 'bbox'; give it each
            # cluster's base character so a mark does not change its class.
            stored = sorted(clusters, key=lambda c: c['index'])
            proxies = [{'c': c['c'][:1], 'bbox': c['bbox'], 'cluster': c} for c in stored]
            clusters = [proxy['cluster'] for proxy in logical_order(proxies)]
            parts = []
            for cluster, following in zip(clusters, clusters[1:] + [None]):
                parts.append(f"<{cluster['c'].encode('utf-16-be').hex()}>")
                if following is not None:
                    pen = position[id(cluster)] + _units(cluster) * cell
                    parts.append(f'{-(position[id(following)] - pen) / cell * _GLYPH_WIDTH:.1f}')
            shown = '[' + ' '.join(parts) + '] TJ'
        else:
            # The stored order, as MuPDF reports the line.
            clusters.sort(key=lambda c: c['index'])
            shown = f"<{''.join(c['c'] for c in clusters).encode('utf-16-be').hex()}> Tj"

        # Text space to page space along the line's direction, then to PDF space.
        # A TJ starts at its first cluster's cell; a Tj runs from the left.
        first = position[id(clusters[0])] if rtl else min(position[id(c)] for c in clusters)
        ox, oy = clusters[0]['origin']
        along = first - (ox * dx + oy * dy)
        tm = fitz.Matrix(dx, dy, dy, -dx, ox + along * dx, oy + along * dy) * matrix
        out.append(
            f'/GLF0 {size:.3f} Tf {100 * cell / natural:.3f} Tz '
            f'{tm.a:.5f} {tm.b:.5f} {tm.c:.5f} {tm.d:.5f} {tm.e:.3f} {tm.f:.3f} Tm {shown}'
        )
    out.append('ET')
    return '\n'.join(out)


_TOUNICODE = b"""/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Adobe-Identity-UCS def
/CMapType 2 def
1 begincodespacerange
<0000> <FFFF>
endcodespacerange
1 beginbfrange
<0000> <FFFF> <0000>
endbfrange
endcmap
CMapName currentdict /CMap defineresource pop
end
end"""


def add_glyphless_font(document) -> int:
    """
    Adds the glyphless font for an invisible text layer and returns its xref.

    The same construction Tesseract uses: a Type0 font with Identity-H
    encoding whose CIDs are UTF-16 code units, an identity ToUnicode map so
    extraction recovers the text, and an embedded TrueType font whose every
    glyph is blank. Embedding it matters: PDF editors warn about a font they
    cannot find even when nothing visible uses it.
    """
    def new_object(definition: str, stream: bytes | None = None) -> int:
        xref = document.get_new_xref()
        document.update_object(xref, definition)
        if stream is not None:
            document.update_stream(xref, stream)
        return xref

    to_unicode = new_object('<<>>', _TOUNICODE)
    font_file = new_object('<<>>', _glyphless_truetype())
    # Every CID maps to glyph 1, the blank one.
    cid_to_gid = new_object('<<>>', b'\x00\x01' * 0x10000)
    descriptor = new_object(
        '<</Type/FontDescriptor/FontName/GlyphLessFont/Flags 5/FontBBox[0 0 500 1000]'
        f'/ItalicAngle 0/Ascent 1000/Descent 0/CapHeight 1000/StemV 80/FontFile2 {font_file} 0 R>>'
    )
    cid_font = new_object(
        '<</Type/Font/Subtype/CIDFontType2/BaseFont/GlyphLessFont'
        '/CIDSystemInfo<</Registry(Adobe)/Ordering(Identity)/Supplement 0>>'
        f'/FontDescriptor {descriptor} 0 R/DW {_GLYPH_WIDTH}/CIDToGIDMap {cid_to_gid} 0 R>>'
    )
    return new_object(
        '<</Type/Font/Subtype/Type0/BaseFont/GlyphLessFont/Encoding/Identity-H'
        f'/DescendantFonts[{cid_font} 0 R]/ToUnicode {to_unicode} 0 R>>'
    )


def _glyphless_truetype() -> bytes:
    """A minimal TrueType font: .notdef and one blank glyph, 'space'."""
    units_per_em = 1000
    name_strings = {1: 'GlyphLessFont', 2: 'Regular', 4: 'GlyphLessFont', 6: 'GlyphLessFont'}

    head = struct.pack(
        '>IIIIHHqqhhhhHHhhh',
        0x00010000, 0x00010000, 0, 0x5F0F3CF5,      # version, revision, checksum adjustment, magic
        0x000B, units_per_em, 0, 0,                  # flags, unitsPerEm, created, modified
        0, 0, _GLYPH_WIDTH, units_per_em,            # xMin, yMin, xMax, yMax
        0, 3, 2, 0, 0,                               # macStyle, lowestRecPPEM, direction hint, short loca, glyf format
    )
    hhea = struct.pack(
        '>IhhhHhhhhhhhhhhhH',
        0x00010000, units_per_em, 0, 0, _GLYPH_WIDTH,  # version, ascender, descender, lineGap, advanceWidthMax
        0, 0, 0, 1, 0, 0,                              # minLSB, minRSB, xMaxExtent, caret rise, run, offset
        0, 0, 0, 0, 0, 2,                              # reserved x4, metricDataFormat, numberOfHMetrics
    )
    maxp = struct.pack('>IHHHHHHHHHHHHHH', 0x00010000, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0)
    hmtx = struct.pack('>HhHh', _GLYPH_WIDTH, 0, _GLYPH_WIDTH, 0)
    # .notdef has no data; glyph 1 is a record with zero contours.
    glyf = struct.pack('>hhhhh', 0, 0, 0, 0, 0)
    loca = struct.pack('>HHH', 0, 0, len(glyf) // 2)
    # (3,1) format 4 subtable mapping U+0020 to glyph 1, plus the mandatory
    # terminating segment. Readers warn about a subtable with no mappings.
    subtable = struct.pack(
        '>HHHHHHHHHHHHhhHH',
        4, 32, 0, 4, 4, 1, 0,     # format, length, language, segCountX2, searchRange, entrySelector, rangeShift
        0x0020, 0xFFFF, 0,        # endCode[2], reservedPad
        0x0020, 0xFFFF,           # startCode[2]
        1 - 0x0020, 1,            # idDelta[2]
        0, 0,                     # idRangeOffset[2]
    )
    cmap = struct.pack('>HHHHI', 0, 1, 3, 1, 12) + subtable
    # Format 2 names the glyphs (.notdef and the standard 'space', index 3);
    # format 3 carries no names and some readers warn about that.
    post = struct.pack('>IIhhIIIIIHHH', 0x00020000, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 3)

    records, strings = b'', b''
    for name_id, text in name_strings.items():
        encoded = text.encode('utf-16-be')
        records += struct.pack('>HHHHHH', 3, 1, 0x409, name_id, len(encoded), len(strings))
        strings += encoded
    name = struct.pack('>HHH', 0, len(name_strings), 6 + len(records)) + records + strings

    tables = {
        b'cmap': cmap, b'glyf': glyf, b'head': head, b'hhea': hhea, b'hmtx': hmtx,
        b'loca': loca, b'maxp': maxp, b'name': name, b'post': post,
    }
    count = len(tables)
    power = 1 << (count.bit_length() - 1)
    header = struct.pack('>IHHHH', 0x00010000, count, power * 16, power.bit_length() - 1, (count - power) * 16)

    directory, body, head_offset = b'', b'', 0
    start = len(header) + 16 * count
    for tag in sorted(tables):
        data = tables[tag]
        if tag == b'head':
            head_offset = start + len(body)
        directory += struct.pack('>4sIII', tag, _checksum(data), start + len(body), len(data))
        body += data + b'\0' * (-len(data) % 4)
    font = bytearray(header + directory + body)
    struct.pack_into('>I', font, head_offset + 8, (0xB1B0AFBA - _checksum(bytes(font))) & 0xFFFFFFFF)
    return bytes(font)


def _checksum(data: bytes) -> int:
    data += b'\0' * (-len(data) % 4)
    return sum(struct.unpack(f'>{len(data) // 4}I', data)) & 0xFFFFFFFF


def _filter_text(document, page, sanitize_options) -> None:
    """Runs a text filter over the page's content and its form XObjects."""
    # instance_forms gives each form use its own copy, so a form drawn twice
    # with different clips is filtered per use.
    options = pymupdf._make_PdfFilterOptions(instance_forms=1, ascii=1, sanitize=1, sopts=sanitize_options)
    mupdf.pdf_filter_page_contents(pymupdf._as_pdf_document(document), pymupdf._as_pdf_page(page), options)


def _mupdf_page_matrix(page):
    """MuPDF's PDF-space to page-space matrix (MediaBox offset, flip, rotation)."""
    matrix = mupdf.FzMatrix()
    mupdf.pdf_page_transform(pymupdf._as_pdf_page(page), mupdf.FzRect(), matrix)
    return matrix


def _page_matrix(page) -> fitz.Matrix:
    m = _mupdf_page_matrix(page)
    return fitz.Matrix(m.a, m.b, m.c, m.d, m.e, m.f)


def _glyph_text(ucsbuf, ucslen: int) -> str:
    """Reads the Unicode text of one glyph from the filter's int buffer."""
    # SWIG hands the C `int *` over as an opaque pointer object.
    address = int(ucsbuf)
    return ''.join(
        chr(ctypes.c_int.from_address(address + i * ctypes.sizeof(ctypes.c_int)).value)
        for i in range(ucslen)
    )


def _rgb(colorspace, color) -> tuple[float, float, float]:
    if not colorspace:
        return (0.0, 0.0, 0.0)
    rgb = mupdf.FzColorspace(mupdf.FzColorspace.Fixed_RGB)
    params = mupdf.FzColorParams()
    return tuple(mupdf.ll_fz_convert_color(colorspace, color, rgb.m_internal, None, params.internal())[:3])


# A BT ... ET text object, as tokens: the filter writes normalized ASCII content.
_TEXT_OBJECT = re.compile(rb'(?<![^\s\]\)>])BT\b.*?\bET\b', re.S)


def _page_forms(document, xref: int, seen: set[int] | None = None) -> list[int]:
    """Form XObjects reachable from a page or form, depth first."""
    seen = set() if seen is None else seen
    kind, value = document.xref_get_key(xref, 'Resources/XObject')
    if kind == 'xref':
        value = document.xref_object(int(value.split()[0]), compressed=True)
    elif kind != 'dict':
        return []
    found = []
    for ref in re.findall(r'(\d+) 0 R', value):
        child = int(ref)
        if child in seen or document.xref_get_key(child, 'Subtype')[1] != '/Form':
            continue
        seen.add(child)
        found.append(child)
        found += _page_forms(document, child, seen)
    return found
