"""Read a downloaded PPTX; check actual text and basic geometry, no Office automation."""
import sys
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def inspect(path, terms):
    prs = Presentation(path)
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                text.append(shape.text)
            if shape.has_table:
                text.extend(cell.text for row in shape.table.rows for cell in row.cells)
            if shape.shape_type != MSO_SHAPE_TYPE.GROUP and (shape.left < -10000 or shape.top < -10000 or shape.left + shape.width > prs.slide_width + 10000 or shape.top + shape.height > prs.slide_height + 10000):
                raise AssertionError("PPTX shape extends outside slide")
    joined = "\n".join(text)
    for term in terms:
        if term not in joined:
            raise AssertionError(f"Expected exported text absent: {term}")
    print(f"Checked {len(prs.slides)} slides; text parity only, rendered layout review outstanding")


if __name__ == "__main__":
    inspect(sys.argv[1], sys.argv[2:])
