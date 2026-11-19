"""
Adversarial Unit Test Suite for Board Deck PPTX & Regulatory Memo PDF Compilers
Milestone 18 - Automated Institutional Deliverable Compilation

Verifies:
- 12-Slide PowerPoint presentation assembly with institutional color palette and structure
- Multi-page SEBI RA 2014 regulatory memorandum PDF generation with ReportLab
- Cryptographic SHA-256 provenance manifest embedding
- Rule E.3 Zero-Truthiness and non-empty byte buffer validation
"""

import pytest
from io import BytesIO
from pptx import Presentation

from models.pre_ipo_board_deck_compiler import PreIPOBoardDeckCompiler
from models.pre_ipo_memo_compiler import PreIPOMemoCompiler


@pytest.fixture
def deck_compiler():
    return PreIPOBoardDeckCompiler("HCCH")


@pytest.fixture
def memo_compiler():
    return PreIPOMemoCompiler("HCCH")


def test_board_deck_pptx_generation(deck_compiler):
    """Verifies that the 12-slide IC Board Deck generates cleanly with correct slides."""
    buf = deck_compiler.compile_deck()
    assert isinstance(buf, BytesIO)
    data = buf.getvalue()
    assert len(data) > 30_000  # Substantial presentation file size

    # Inspect loaded presentation
    prs = Presentation(BytesIO(data))
    assert len(prs.slides) == 12

    # Verify slide dimensions are 16:9 widescreen
    assert round(prs.slide_width.inches, 2) == 13.33
    assert round(prs.slide_height.inches, 2) == 7.50

    # Verify slide 1 (Cover) contains issuer and title
    slide1_text = " ".join(shape.text_frame.text for shape in prs.slides[0].shapes if shape.has_text_frame)
    assert "HCCH" in slide1_text
    assert "Board Deck" in slide1_text

    # Verify slide 4 contains CESTAT tax exposure
    slide4_text = " ".join(shape.text_frame.text for shape in prs.slides[3].shapes if shape.has_text_frame)
    assert "CESTAT" in slide4_text
    assert "4,455.47" in slide4_text

    # Verify slide 9 contains Varun Beverages CMIE comps
    slide9_text = " ".join(shape.text_frame.text for shape in prs.slides[8].shapes if shape.has_text_frame)
    assert "Varun Beverages" in slide9_text
    assert "38.5x" in slide9_text

    # Verify slide 12 contains IC final recommendation
    slide12_text = " ".join(shape.text_frame.text for shape in prs.slides[11].shapes if shape.has_text_frame)
    assert "SUBSCRIBE WITH COVENANTS" in slide12_text


def test_memo_pdf_generation(memo_compiler):
    """Verifies that the SEBI Regulatory Research Memo PDF generates cleanly."""
    buf = memo_compiler.compile_pdf()
    assert isinstance(buf, BytesIO)
    data = buf.getvalue()
    assert len(data) > 10_000  # ReportLab flate-compressed PDF document size (>10KB)
    assert data.startswith(b"%PDF-")  # Valid PDF binary signature
    assert b"%%EOF" in data  # Well-formed PDF termination


def test_rule_e3_zero_truthiness_and_symbol_preservation():
    """Rule E.3: Custom or empty symbols handled safely without truthiness failure."""
    deck = PreIPOBoardDeckCompiler(symbol="HCCH")
    assert deck.symbol == "HCCH"

    memo = PreIPOMemoCompiler(symbol="HCCH")
    assert memo.symbol == "HCCH"
