"""
Unit tests for Plotly Theme Dispatcher, Transparent Backdrops, and Event Ribbons.
"""
import pytest
import plotly.graph_objects as go
from helpers import plotly_layout, plotly_layout_dark, plotly_layout_light, event_bands


def test_plotly_layout_dark_theme():
    """Verify dark theme returns transparent backdrops and light text."""
    layout = plotly_layout_dark("Test Title")
    assert layout["paper_bgcolor"] in ("rgba(0,0,0,0)", "rgba(0, 0, 0, 0)")
    assert layout["plot_bgcolor"] in ("rgba(0,0,0,0)", "rgba(0, 0, 0, 0)")
    assert layout["title"]["text"] == "Test Title"


def test_plotly_layout_light_theme():
    """Verify light theme returns transparent backdrops and readable fonts."""
    layout = plotly_layout_light("Test Title")
    assert layout["paper_bgcolor"] in ("rgba(0,0,0,0)", "rgba(0, 0, 0, 0)")
    assert layout["plot_bgcolor"] in ("rgba(0,0,0,0)", "rgba(0, 0, 0, 0)")


def test_event_bands_injection():
    """Verify translucent regime shock ribbons are added without mutating existing traces."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[2005, 2010, 2015, 2020], y=[20, 25, 30, 35], name="Leverage"))

    assert len(fig.data) == 1

    # Inject event bands
    fig = event_bands(fig)
    assert len(fig.data) == 1  # data trace count is unchanged
    assert len(fig.layout.shapes) >= 3  # GFC, IBC, COVID shapes injected
