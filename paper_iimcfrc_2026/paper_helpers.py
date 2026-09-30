"""
Low-level python-docx helpers for generating academic/conference papers.

Copy this file into your paper project's docs/ folder (next to your
generate_paper_docx_vN.py script) and import from it directly:

    from paper_helpers import ap, heading, bcp, hline, _th, _td, _r

Do not import this across directories via sys.path tricks -- copy it in.
When a bug fix lands in the canonical copy at
~/.claude/toolkits/academic-paper-docx/scripts/paper_helpers.py, re-copy it
into any project you're actively revising.

All text runs default to Times New Roman, 12pt, double-spaced (ls=2.0) --
the near-universal baseline for conference/journal submissions. Override
per call for title pages, captions, table cells, and references, which are
conventionally smaller and single-spaced even in an otherwise
double-spaced manuscript.

Two OOXML gotchas this module works around (see ooxml-gotchas.md for the
full explanation):
  1. hline() inserts w:pBdr as the FIRST child of w:pPr (before
     w:spacing/w:ind), not appended after -- appending after produces
     schema-invalid XML that Word tolerates but a strict validator rejects.
  2. Nothing here emits w:cols. For a single-column paper, python-docx
     sections already default to one column -- don't fight the ordering
     rules of w:cols inside w:sectPr by trying to set it explicitly.
"""

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _r(para, text, bold=False, italic=False, size=12, color=None, font='Times New Roman'):
    """Add a styled run to a paragraph."""
    r = para.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    r.font.name = font
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return r


def ap(doc, text, bold=False, italic=False, size=12,
       align=WD_ALIGN_PARAGRAPH.JUSTIFY, sb=0, sa=5, fi=0, ls=2.0):
    """
    Add a body paragraph: justified by default, double-spaced by default,
    with an optional first-line indent.

    Args:
        sb, sa: space before/after, in points.
        fi: first-line indent, in points (14 approximates a standard
            paragraph indent at 12pt body text; use 0 for block style).
        ls: line spacing multiplier (2.0 = double, 1.5 = 1.5x, 1.0 = single).
            Pass ls=1.0 for captions, table notes, and other short text
            that shouldn't visually double-space.
    """
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.line_spacing = ls
    if fi:
        p.paragraph_format.first_line_indent = Pt(fi)
    _r(p, text, bold=bold, italic=italic, size=size)
    return p


def heading(doc, text, level=1, sb=10, sa=4):
    """
    Add a section heading. Level 1 = 14pt bold ALL CAPS (top-level section,
    e.g. "1. INTRODUCTION"); level 2 = 12pt bold sentence case (subsection,
    e.g. "2.1  Sample Construction").
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14 if level == 1 else 12)
    if level == 1:
        r.font.all_caps = True
    return p


def bcp(doc, lead, rest, sb=0, sa=4, ls=2.0):
    """
    Bold-lead-in paragraph: the standard academic convention for an
    enumerated finding, term, or persona -- "Lead.  Explanation follows in
    normal weight." Used heavily for "for each of N pain points / findings
    / personas" sections.
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_before = Pt(sb)
    p.paragraph_format.space_after = Pt(sa)
    p.paragraph_format.line_spacing = ls
    _r(p, lead + '  ', bold=True, size=12)
    _r(p, rest, size=12)
    return p


def hline(doc):
    """
    Add a horizontal rule via OOXML w:pBdr (bottom paragraph border).
    Commonly used under the title block and abstract.
    """
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single')
    bot.set(qn('w:sz'), '6')
    bot.set(qn('w:space'), '1')
    bot.set(qn('w:color'), '000000')
    pBdr.append(bot)
    pPr.insert(0, pBdr)  # pBdr must precede spacing/ind per OOXML CT_PPrBase order
    return p


def _th(tbl, row_idx, vals, sz=12):
    """Fill a table row with bold header text."""
    row = tbl.rows[row_idx]
    for j, v in enumerate(vals):
        c = row.cells[j]
        c.text = v
        for pp in c.paragraphs:
            for rr in pp.runs:
                rr.bold = True
                rr.font.size = Pt(sz)
                rr.font.name = 'Times New Roman'


def _td(tbl, row_idx, vals, sz=12):
    """Fill a table row with normal-weight data text."""
    row = tbl.rows[row_idx]
    for j, v in enumerate(vals):
        c = row.cells[j]
        c.text = v
        for pp in c.paragraphs:
            for rr in pp.runs:
                rr.font.size = Pt(sz)
                rr.font.name = 'Times New Roman'
