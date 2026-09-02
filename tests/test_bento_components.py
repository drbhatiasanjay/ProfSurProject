"""
Unit tests for Bento KPI Card generation, SVG Sparklines, and Stage Badges.
"""
import pytest
from helpers import (
    render_sparkline_svg,
    render_bento_kpi,
    render_stage_badge,
    render_citation_pill,
)


def test_sparkline_svg_generation():
    """Verify SVG polyline coordinates are computed within bounds."""
    data = [10.0, 14.5, 12.0, 18.2, 22.0, 20.5]
    svg_html = render_sparkline_svg(data, width=240, height=36)

    assert "<svg" in svg_html
    assert "class=\"sparkline-svg\"" in svg_html
    assert "<polyline" in svg_html
    assert "points=\"" in svg_html


def test_sparkline_svg_edge_cases():
    """Gracefully handle empty, flat, or single-item data series."""
    assert render_sparkline_svg([]) == ""
    assert render_sparkline_svg([15.0]) == ""
    # Flat series should not raise divide by zero
    flat_svg = render_sparkline_svg([10.0, 10.0, 10.0])
    assert "<polyline" in flat_svg


def test_bento_kpi_card_html_output():
    """Verify HTML structure of the Bento KPI capsule."""
    html = render_bento_kpi(
        title="Average Leverage",
        value="34.2%",
        delta="+1.4pp YoY",
        sparkline_data=[30.0, 31.5, 32.8, 34.2],
        percentile=72.0,
        tag="401 FIRMS"
    )

    assert "class=\"bento-card\"" in html
    assert "Average Leverage" in html
    assert "34.2%" in html
    assert "+1.4pp YoY" in html
    assert "delta-up" in html
    assert "72%" in html
    assert "401 FIRMS" in html


def test_stage_badge_semantic_colors():
    """Verify that render_stage_badge returns correct colors for Dickinson stages."""
    intro_badge = render_stage_badge("Introduction")
    mature_badge = render_stage_badge("Mature")
    shakeout_badge = render_stage_badge("Shakeout")

    assert "Intro" in intro_badge
    assert "Mature" in mature_badge
    assert "Shakeout" in shakeout_badge
    assert "stage-badge" in mature_badge


def test_citation_pill_markup():
    """Verify that academic citations render as clickable pills."""
    pill_html = render_citation_pill("Rajan & Zingales (1995)", "rajan_zingales_1995")
    assert "citation-tag" in pill_html
    assert "Rajan &amp; Zingales (1995)" in pill_html or "Rajan & Zingales (1995)" in pill_html
    assert "data-paper=\"rajan_zingales_1995\"" in pill_html
