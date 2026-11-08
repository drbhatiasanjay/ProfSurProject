"""Exports consume one frozen evidence snapshot; no mutable-data recalculation."""
import io
import json


def render_page(content,page_number):
    """Bounded-resolution image, with explicit handles for supported PDFium versions."""
    import pypdfium2 as pdfium
    document=pdfium.PdfDocument(content)
    try:
        page=document[int(page_number)-1]
        try:
            width,height=page.get_size()
            scale=min(1.25,(4_000_000/max(1,width*height))**0.5)
            bitmap=page.render(scale=scale)
            try:
                return bitmap.to_pil().copy()
            finally:
                bitmap.close()
        finally:
            page.close()
    finally:
        document.close()


def export_json(snapshot):
    return json.dumps(snapshot,indent=2,ensure_ascii=False,allow_nan=False).encode("utf-8")


def export_pptx(snapshot):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    presentation=Presentation()
    presentation.slide_width=Inches(13.333)
    presentation.slide_height=Inches(7.5)
    def slide(title,lines):
        item=presentation.slides.add_slide(presentation.slide_layouts[1])
        item.shapes.title.text=title
        frame=item.placeholders[1].text_frame
        frame.clear()
        for index,line in enumerate(lines):
            paragraph=frame.paragraphs[0] if index==0 else frame.add_paragraph()
            paragraph.text=str(line)
            paragraph.font.size=Pt(16)
        item.notes_slide.notes_text_frame.text="Snapshot "+snapshot["id"]+" | "+snapshot["review_policy"]
    slide(snapshot["company_name"]+" · Evidence review",["Cutoff: "+snapshot["cutoff"],"Snapshot: "+snapshot["id"],snapshot["review_policy"],snapshot["assessment"]["qualification"],"Required applicable slots: "+str(snapshot["assessment"]["applicable_slots"]),"Accepted required slots: "+str(snapshot["assessment"]["accepted_required_slots"])])
    for item in snapshot["assessment"]["questions"]:
        slide(item["question"]+" · "+item["period"],[item["state"],item["observation"],item["interpretation"],"Next action: "+item["next_action"],"Fact bindings: "+", ".join(item["fact_ids"])])
    for start in range(0,len(snapshot["assessment"]["gaps"]),6):
        slide("Missing data and evidence",[g["fact_id"]+" · "+g["reason"] for g in snapshot["assessment"]["gaps"][start:start+6]])
    for start in range(0,len(snapshot.get("actions",[])),3):
        slide("Diligence actions",[a["question"]+" · "+a.get("status","OPEN")+" · Owner: "+a["assignee"]+" · Due: "+a["due"]+" · "+a["next_action"] for a in snapshot["actions"][start:start+3]])
    reviewed=[f for f in snapshot["facts"] if f["id"] in snapshot["assessment"]["accepted_fact_revisions"]]
    for fact in reviewed:
        source=fact.get("source",{})
        slide("Reviewed fact · "+fact["id"],["Value: "+str(fact["value"]),"Context: "+json.dumps(fact["context"],ensure_ascii=False),"Revision: "+str(fact["revision"]),"Source: "+source.get("id",""),"PDF page: "+str(source.get("page",""))+" · "+source.get("locator",""),"Quote: "+source.get("quote","")[:900]])
    slide("Source manifest",[s["title"]+" · "+s["filing_type"]+" · "+s["version"]+" · SHA256 "+s["sha256"] for s in snapshot["sources"]] or ["No retained source: source-qualified conclusions remain blocked."])
    slide("Methodology references",[r["title"]+" · "+r["url"]+" · "+r["scope"] for r in snapshot["assessment"].get("methodology_references",[])])
    buffer=io.BytesIO(); presentation.save(buffer)
    return buffer.getvalue()
