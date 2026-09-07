"""Regression checks for Streamlit widget identity in Stata Studio."""

import ast
from pathlib import Path


def test_static_button_labels_have_unique_widget_identity():
    source = Path("pages/23_stata_studio.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    buttons = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "button":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        label = node.args[0].value
        key = next((kw.value.value for kw in node.keywords if kw.arg == "key" and isinstance(kw.value, ast.Constant)), None)
        buttons.append((label, key))

    labels = [label for label, _ in buttons]
    duplicate_labels = {label for label in labels if labels.count(label) > 1}
    assert all(key for label, key in buttons if label in duplicate_labels)

    keys = [key for _, key in buttons if key]
    assert len(keys) == len(set(keys))
