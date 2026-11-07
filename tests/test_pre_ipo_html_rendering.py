"""Regression for nested terminal HTML appearing as Markdown code blocks."""
import ast
from pathlib import Path

import pytest

markdown_it = pytest.importorskip("markdown_it")
MarkdownIt = markdown_it.MarkdownIt

from utils import html_blocks


PAGE = Path(__file__).resolve().parents[1] / "pages/27_pre_ipo_drhp.py"


def test_html_after_blank_lines_stays_html(monkeypatch):
    rendered = []
    monkeypatch.setattr(html_blocks.st, "markdown", lambda html, **kw: rendered.append((html, kw)))
    html_blocks.render_html('''
        <div class="narrative-card">
            <p>Observation</p>

            <div>Evidence &amp; action</div>
        </div>
    ''')
    html, options = rendered[0]
    tokens = MarkdownIt("commonmark", {"html": True}).parse(html)
    assert options == {"unsafe_allow_html": True}
    assert not any(t.type in {"code_block", "fence"} for t in tokens)
    assert "Evidence &amp; action" in html


def test_every_narrative_field_renders_without_code_blocks(monkeypatch):
    tree = ast.parse(PAGE.read_text(encoding="utf-8-sig"))
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "render_six_point_narrative")
    namespace = {"render_html": html_blocks.render_html}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(PAGE), "exec"), namespace)
    rendered = []
    monkeypatch.setattr(html_blocks.st, "markdown", lambda html, **kw: rendered.append(html))
    fields = ("what_you_see", "why_it_matters", "evidence_basis", "alternative_explanations", "call_to_action", "inflection_triggers")
    values = {field: "Line one\n\n    Line two: " + field for field in fields}
    namespace["render_six_point_narrative"](values, "CFO")
    html = rendered[0]
    tokens = MarkdownIt("commonmark", {"html": True}).parse(html)
    assert not any(t.type in {"code_block", "fence"} for t in tokens)
    assert all(field in html for field in fields)
    assert "CFO Lens" in html


def test_terminal_uses_html_renderer_for_all_cards():
    tree = ast.parse(PAGE.read_text(encoding="utf-8-sig"))
    raw_html_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                     and n.func.value.id == "st" and n.func.attr == "markdown"
                     and any(k.arg == "unsafe_allow_html" and isinstance(k.value, ast.Constant)
                             and k.value.value is True for k in n.keywords)]
    assert not raw_html_calls
