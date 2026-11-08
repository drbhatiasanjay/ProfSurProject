"""Create portable synthetic documents; no issuer financial figures invented."""
import io
import json
from pathlib import Path
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter


def generate(destination):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    lines = ["SYNTHETIC FUNCTIONAL TEST ONLY - NOT ISSUER DATA", "FY24 consolidated IND AS INR crore",
             "Revenue from operations 1234.00", "EBITDA 234.00", "Profit after tax 89.00",
             "Cash flow from operations 100.00", "Net worth 678.00", "Cash and equivalents 50.00",
             "Secured term loans 200.00", "Table 1: CFO 100; EBITDA 234; revenue 1234"]
    for name, document_lines in {"known-values.pdf": lines,
        "zeros.pdf": [lines[0], lines[1], "Revenue from operations 1234.00", "EBITDA 0.00", "Cash flow from operations 0.00"],
        "mixed-units.pdf": [lines[0], "FY24 consolidated IND AS INR crore", "Revenue from operations 1234.00",
                            "Cash flow statement INR million", "Cash flow from operations 200.00"],
        "negative-values.pdf": [lines[0], lines[1], "Revenue from operations 1234.00", "Profit after tax (89.00)", "Cash flow from operations -100.00"],
        "companion.pdf": [lines[0], "Synthetic governance policy: existence does not establish compliance."],
        "html-payload.pdf": [lines[0], "<script>alert('SYNTHETIC')</script>", "<div style='color:red'>INERT DOCUMENT TEXT</div>"]}.items():
        c = canvas.Canvas(str(dest / name))
        y = 760
        for line in document_lines:
            c.drawString(35, y, line)
            y -= 26
        c.save()
    c = canvas.Canvas(str(dest / "multi-page.pdf"))
    for number in range(1, 24):
        c.drawString(40, 750, f"SYNTHETIC PAGE {number}: FY24 INR crore CFO {number}")
        c.showPage()
    c.save()
    image = Image.new("RGB", (1300, 1700), "white")
    draw = ImageDraw.Draw(image)
    for idx, line in enumerate(lines):
        draw.text((50, 100 + idx * 60), line, fill="black", font_size=28)
    c = canvas.Canvas(str(dest / "scanned.pdf"))
    c.drawImage(ImageReader(image), 0, 0, width=612, height=792)
    c.save()
    writer = PdfWriter()
    writer.append(PdfReader(str(dest / "known-values.pdf")))
    writer.encrypt("synthetic-not-a-user-password")
    with (dest / "encrypted.pdf").open("wb") as output:
        writer.write(output)
    (dest / "not-a-pdf.pdf").write_text("This is not a PDF", encoding="utf-8")
    (dest / "corrupt.pdf").write_bytes(b"%PDF-1.4\ntruncated")
    (dest / "oversize.pdf").write_bytes((dest / "known-values.pdf").read_bytes() + b"\n%" + b"x" * (26 * 1024 * 1024))
    (dest / "invalid-case.json").write_text('{"schema_version": 1, "company": NaN}')
    (dest / "catalogue.csv").write_text("Table,Field Name,Indicator\nSynthetic,CFO,Cash flow from operations\n")
    (dest / "gold.json").write_text(json.dumps({"qualification": "Synthetic expected values specified before extraction", "FY24": {
        "revenue_ops_cr": 1234, "ebitda_cr": 234, "pat_cr": 89, "cfo_cr": 100, "net_worth_cr": 678}}))


if __name__ == "__main__":
    generate(sys.argv[1])
