"""
PPTX Generator — assembles Board Deck from topic data dicts.

Uses python-pptx + kaleido (Plotly → PNG → slide).
Each Plotly figure is exported as a high-res PNG and embedded as a picture shape.
Text insight bullets are added as a text box below each chart.
"""

from __future__ import annotations
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO

logger = logging.getLogger(__name__)

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

from models.board_export import TOPIC_BUILDERS, TOPIC_LABELS

# Slide dimensions — 16:9 widescreen
SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

# Brand colours (hex → int tuples for python-pptx)
_COLOR_HEADER_BG = RGBColor(0x0D, 0x94, 0x88)   # PRIMARY teal
_COLOR_HEADER_FG = RGBColor(0xFF, 0xFF, 0xFF)
_COLOR_BODY_FG   = RGBColor(0x1F, 0x29, 0x37)
_COLOR_BULLET_FG = RGBColor(0x37, 0x4A, 0x5F)
_COLOR_ACTION_FG = RGBColor(0x0D, 0x94, 0x88)

# Layout metrics
_HEADER_H   = Inches(0.75)
_FOOTER_H   = Inches(0.30)
_MARGIN_L   = Inches(0.35)
_MARGIN_R   = Inches(0.35)
_CHART_TOP  = _HEADER_H + Inches(0.10)
_CHART_W    = SLIDE_W - _MARGIN_L - _MARGIN_R
_CHART_H    = Inches(4.00)
_TEXT_TOP   = _CHART_TOP + _CHART_H + Inches(0.10)
_TEXT_H     = SLIDE_H - _TEXT_TOP - _FOOTER_H - Inches(0.05)


def _add_header(slide, title: str, company_name: str) -> None:
    """Dark teal header bar with slide title and company name."""
    txBox = slide.shapes.add_textbox(0, 0, SLIDE_W, _HEADER_H)
    tf = txBox.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = f"{company_name}  ·  {title}"
    run.font.size = Pt(14)
    run.font.bold = True
    run.font.color.rgb = _COLOR_HEADER_FG
    # Background fill
    from pptx.util import Pt as _Pt
    fill = txBox.fill
    fill.solid()
    fill.fore_color.rgb = _COLOR_HEADER_BG


def _add_footer(slide, page_num: int, total: int) -> None:
    """Subtle footer with page number."""
    y = SLIDE_H - _FOOTER_H
    txBox = slide.shapes.add_textbox(_MARGIN_L, y, SLIDE_W - _MARGIN_L - _MARGIN_R, _FOOTER_H)
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = f"Slide {page_num} of {total}  ·  LifeCycle Leverage Dashboard  ·  ProfSur Analytics"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x9C, 0xA3, 0xAF)


def _add_chart_image(slide, fig, top=None, height=None) -> None:
    """Export a Plotly figure as PNG and embed it on the slide."""
    top = top if top is not None else _CHART_TOP
    height = height if height is not None else _CHART_H
    # Slides use a white canvas even when the interactive application is dark.
    import plotly.graph_objects as go
    from helpers import plotly_layout_light
    export_fig = go.Figure(fig)
    export_fig.update_layout(**dict(plotly_layout_light(title=fig.layout.title.text or "", height=600), paper_bgcolor="white", plot_bgcolor="white"))
    export_fig.update_traces(number_font_color="#1F2937", title_font_color="#1F2937", selector=dict(type="indicator"))
    img_bytes = export_fig.to_image(format="png", width=1600, height=600, scale=2)
    slide.shapes.add_picture(
        BytesIO(img_bytes),
        _MARGIN_L, top, _CHART_W, height,
    )


def _add_table(slide, df, top=None) -> None:
    """Add a pandas DataFrame as a PPTX table."""
    if df is None or df.empty:
        return
    top = top if top is not None else _CHART_TOP
    rows, cols = len(df) + 1, len(df.columns)
    col_w = _CHART_W / cols
    tbl = slide.shapes.add_table(rows, cols, _MARGIN_L, top,
                                  _CHART_W, Inches(0.55 * rows)).table
    for column in tbl.columns:
        column.width = int(col_w)
    # Header row
    for j, col_name in enumerate(df.columns):
        cell = tbl.cell(0, j)
        cell.text = str(col_name)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _COLOR_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = _COLOR_HEADER_FG
    # Data rows
    for i, (_, row) in enumerate(df.iterrows()):
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.text = str(val) if val is not None else ""
            p = cell.text_frame.paragraphs[0]
            run = p.runs[0] if p.runs else p.add_run()
            run.font.size = Pt(11)
            run.font.color.rgb = _COLOR_BODY_FG
            if i % 2 == 1:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xF3, 0xF4, 0xF6)


def _add_insights_text(slide, insights: list[str], actions: list[str], *, full_height=False) -> None:
    """Two-column text box: key findings (left) + actions (right)."""
    half_w = (_CHART_W - Inches(0.15)) / 2

    for col_idx, (heading, items, color) in enumerate([
        ("Key Findings", insights, _COLOR_BULLET_FG),
        ("Actions", actions, _COLOR_ACTION_FG),
    ]):
        x = _MARGIN_L + col_idx * (half_w + Inches(0.15))
        txBox = slide.shapes.add_textbox(x, _CHART_TOP if full_height else _TEXT_TOP,
                                       half_w, Inches(5.7) if full_height else _TEXT_H)
        tf = txBox.text_frame
        tf.word_wrap = True

        # Heading
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = heading
        run.font.size = Pt(17 if full_height else 12)
        run.font.bold = True
        run.font.color.rgb = _COLOR_HEADER_BG

        # Bullets
        for item in items[:4]:   # max 4 bullets per column
            p = tf.add_paragraph()
            p.space_before = Pt(3)
            run = p.add_run()
            # Strip markdown bold markers for PPTX plain text
            run.text = "• " + item.replace("**", "")
            run.font.size = Pt(16 if full_height else 10)
            run.font.color.rgb = color


def _cover_slide(prs: Presentation, company_info: dict, selected_count: int) -> None:
    """Branded cover slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    # Full background block
    bg = slide.shapes.add_textbox(0, 0, SLIDE_W, SLIDE_H)
    bg.fill.solid()
    bg.fill.fore_color.rgb = _COLOR_HEADER_BG

    # Company name (large)
    txt = slide.shapes.add_textbox(Inches(1), Inches(1.8), SLIDE_W - Inches(2), Inches(1.5))
    tf = txt.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = company_info.get("name", "Company")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = _COLOR_HEADER_FG

    # Subtitle
    txt2 = slide.shapes.add_textbox(Inches(1), Inches(3.4), SLIDE_W - Inches(2), Inches(0.8))
    tf2 = txt2.text_frame
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = (
        f"Capital Structure Board Deck  ·  {company_info.get('industry', '')}  ·  "
        f"Life Stage: {company_info.get('current_stage', '')}  ·  "
        f"{selected_count} sections selected  ·  {datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y')}"
    )
    run2.font.size = Pt(14)
    run2.font.color.rgb = RGBColor(0xE0, 0xF2, 0xF1)

    # Footnote
    fn = slide.shapes.add_textbox(Inches(1), Inches(6.6), SLIDE_W - Inches(2), Inches(0.5))
    tf_fn = fn.text_frame
    p_fn = tf_fn.paragraphs[0]
    p_fn.alignment = PP_ALIGN.CENTER
    run_fn = p_fn.add_run()
    run_fn.text = "Generated by LifeCycle Leverage Dashboard — Prof. Surendra Kumar PhD Thesis Platform"
    run_fn.font.size = Pt(9)
    run_fn.font.color.rgb = RGBColor(0xB2, 0xDF, 0xDB)


def build(
    company_df,
    company_info: dict,
    peers_df,
    full_panel,
    stage_summary,
    selected_topics: dict,
    *, warnings=None, topic_data=None,
) -> bytes:
    """
    Build a PPTX presentation and return as bytes.

    selected_topics: {topic_id: bool} — True = include, False = skip.
    """
    warnings = warnings if warnings is not None else []
    sections = []
    for topic_id in sorted(selected_topics.keys()):
        if not selected_topics.get(topic_id):
            continue

        builder = TOPIC_BUILDERS.get(topic_id)
        try:
            section = topic_data[topic_id] if topic_data is not None and topic_id in topic_data else builder(company_df, company_info, peers_df, full_panel, stage_summary)
        except Exception as exc:
            message = f"Topic {topic_id} unavailable ({type(exc).__name__})."
            warnings.append(message)
            section = dict(title=TOPIC_LABELS.get(topic_id, f"Topic {topic_id}"), insights=[message],
                           actions=["Resolve the analysis error before using this section."], tables=[], figs=[])
        sections.append(section)
    return build_sections(company_info, sections, warnings=warnings)


def build_sections(company_info, sections, *, warnings=None):
    """Render prepared sections shared with the preview, with no silent omissions."""
    warnings = warnings if warnings is not None else []
    prs = Presentation()
    prs.slide_width, prs.slide_height = SLIDE_W, SLIDE_H
    _cover_slide(prs, company_info, len(sections))

    def slide_for(section, continuation=""):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
        _add_header(slide, section["title"] + continuation, company_info.get("name", ""))
        slide.notes_slide.notes_text_frame.text = "\n".join(
            [section.get("provenance", ""), *section.get("insights", []), *section.get("actions", [])])
        return slide

    for section in sections:
        for fig in section.get("figs", []):
            slide = slide_for(section)
            try:
                _add_chart_image(slide, fig, height=Inches(5.6))
            except Exception as exc:
                message = f"{section['title']}: chart unavailable ({type(exc).__name__})."
                warnings.append(message)
                _add_insights_text(slide, [message], ["Resolve the chart renderer and regenerate."], full_height=True)
        for table in section.get("tables", []):
            if table is None or table.empty:
                continue
            for col_start in range(0, len(table.columns), 4):
                columns = list(table.columns[:4]) if not col_start else [table.columns[0], *table.columns[col_start:col_start + 4]]
                for start in range(0, len(table), 8):
                    slide = slide_for(section, " | Data" if start == 0 else " | Data continued")
                    try:
                        _add_table(slide, table.loc[:, columns].iloc[start:start + 8])
                    except Exception as exc:
                        message = f"{section['title']}: table unavailable ({type(exc).__name__})."
                        warnings.append(message)
                        _add_insights_text(slide, [message], ["Review the source table and regenerate."], full_height=True)
        insights, actions = section.get("insights", []), section.get("actions", [])
        for start in range(0, max(len(insights), len(actions)), 3):
            slide = slide_for(section, " | Findings" if start == 0 else " | Findings continued")
            _add_insights_text(slide, insights[start:start + 3], actions[start:start + 3], full_height=True)
    total = len(prs.slides)
    for index, slide in enumerate(prs.slides, 1):
        _add_footer(slide, index, total)
    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
