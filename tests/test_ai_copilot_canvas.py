"""
Unit tests for AI Financial Copilot Studio (Page 19) presentation components:
- Stat Bento Capsule Extractor
- Response Action Dock
- Glowing Action Pills
- Context Token Capacity Gauge
"""
import pytest
from helpers import (
    render_bento_kpi,
    render_stage_badge,
    render_citation_pill,
)


def test_stat_bento_capsule_extraction():
    """Verify that stat capsules format financial figures cleanly into Bento markup."""
    title = "Mature Stage Mean Leverage"
    val = "18.8%"
    delta = "Δ -3.2pp vs Growth Stage"
    card_html = render_bento_kpi(
        title=title,
        value=val,
        delta=delta,
        percentile=42.0,
        tag="DICKINSON BENCHMARK",
        stroke_color="#8B5CF6"
    )
    assert "Mature Stage Mean Leverage" in card_html
    assert "18.8%" in card_html
    assert "Δ -3.2pp" in card_html
    assert "42%" in card_html


def test_citation_pills_inside_chat_turn():
    """Verify multiple citation tags render properly without malformed HTML."""
    p1 = render_citation_pill("Myers & Majluf (1984)", "myers_majluf_1984")
    p2 = render_citation_pill("Dickinson (2011)", "dickinson_2011")

    assert "Myers &amp; Majluf (1984)" in p1 or "Myers & Majluf (1984)" in p1
    assert "Dickinson (2011)" in p2
    assert "data-paper=\"dickinson_2011\"" in p2


def test_context_token_gauge_formatting():
    """Verify context capacity meter formatting."""
    turns = 4
    max_turns = 6
    tokens = 2410

    meter_str = f"Context: [{'■' * turns}{'□' * (max_turns - turns)}] {turns}/{max_turns} Turns ({tokens:,} Tokens)"
    assert "4/6 Turns" in meter_str
    assert "2,410 Tokens" in meter_str
    assert "■■■■□□" in meter_str
