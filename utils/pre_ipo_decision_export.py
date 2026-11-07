"""Paginated exports of the same report, without recalculation."""
import io
import json
import textwrap
from pptx import Presentation
from pptx.util import Inches, Pt
from models.pre_ipo_decision.contracts import canonical_json

def export_json(report):
    return canonical_json(report).encode("utf-8")

def export_pptx(report):
    presentation = Presentation()
    presentation.slide_width, presentation.slide_height = Inches(13.333), Inches(7.5)
    sections = [("Decision context", report["context"]), ("Evidence inventory", report["evidence"])]
    sections += [(key.replace("_", " ").title(), value) for key, value in report["results"].items()]
    sections += [("Methodology references", report.get("methodology_references", [])), ("Limitations", report["limitations"])]
    for heading, value in sections:
        raw = json.dumps(value, ensure_ascii=False, indent=2)
        lines = [wrapped for line in raw.splitlines() for wrapped in (textwrap.wrap(line, width=95, replace_whitespace=False) or [""])]
        for start in range(0, len(lines), 20):
            slide = presentation.slides.add_slide(presentation.slide_layouts[6])
            title = slide.shapes.add_textbox(Inches(.5), Inches(.3), Inches(12.2), Inches(.6)).text_frame
            title.text = heading + (" (continued)" if start else "")
            title.paragraphs[0].font.size = Pt(25)
            body = slide.shapes.add_textbox(Inches(.5), Inches(1.1), Inches(12.2), Inches(5.6)).text_frame
            body.word_wrap = True
            for index, line in enumerate(lines[start:start+20]):
                paragraph = body.paragraphs[0] if index == 0 else body.add_paragraph()
                paragraph.text, paragraph.font.size = line, Pt(13)
            footer = slide.shapes.add_textbox(Inches(.5), Inches(7), Inches(12), Inches(.25)).text_frame
            footer.text = report["context_hash"] + " | " + report["method_version"]
            footer.paragraphs[0].font.size = Pt(9)
    output = io.BytesIO()
    presentation.save(output)
    return output.getvalue()
