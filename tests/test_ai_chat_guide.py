"""
Test suite for pages/24_ai_chat_guide.py and related navigation.
"""
import pytest
import os

def test_page_exists():
    path = os.path.join("pages", "24_ai_chat_guide.py")
    assert os.path.isfile(path), "pages/24_ai_chat_guide.py must exist"

def test_page_compilation():
    path = os.path.join("pages", "24_ai_chat_guide.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    compiled = compile(code, path, "exec")
    assert compiled is not None

def test_navigation_registration():
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "24_ai_chat_guide.py" in content
    assert "ai_chat_guide" in content
