"""
Unit tests for Pre-IPO Board Pitch Deck PowerPoint Generator.
"""
import io
import pytest
from pptx import Presentation
from models.pre_ipo_data import PRE_IPO_REGISTRY
from utils.pre_ipo_deck_generator import generate_pre_ipo_board_deck


def test_generate_pre_ipo_board_deck_mankind():
    deal = PRE_IPO_REGISTRY["mankind_pharma"]
    deck_bytes = generate_pre_ipo_board_deck(deal)
    assert len(deck_bytes) > 10000

    # Verify PowerPoint presentation is valid binary and has 8 slides
    prs = Presentation(io.BytesIO(deck_bytes))
    assert len(prs.slides) == 8
    assert prs.slide_width.inches == pytest.approx(13.333, rel=1e-3)  # 16:9 widescreen


def test_generate_pre_ipo_board_deck_afcons():
    deal = PRE_IPO_REGISTRY["afcons_infra"]
    deck_bytes = generate_pre_ipo_board_deck(deal)
    prs = Presentation(io.BytesIO(deck_bytes))
    assert len(prs.slides) == 8

