"""
Unit and integration tests for CSS Design Tokens and Theme Switcher Engine.
"""
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_theme_css_files_exist_and_non_empty():
    """Verify that style_dark.css and style_light.css exist and contain valid rules."""
    dark_path = os.path.join(PROJECT_ROOT, "assets", "style_dark.css")
    light_path = os.path.join(PROJECT_ROOT, "assets", "style_light.css")

    assert os.path.exists(dark_path), "assets/style_dark.css must exist"
    assert os.path.exists(light_path), "assets/style_light.css must exist"

    with open(dark_path, "r", encoding="utf-8") as f:
        dark_content = f.read()
    with open(light_path, "r", encoding="utf-8") as f:
        light_content = f.read()

    assert len(dark_content) > 500, "Dark CSS stylesheet is unexpectedly small"
    assert len(light_content) > 500, "Light CSS stylesheet is unexpectedly small"


def test_css_variables_defined_on_root():
    """Ensure essential CSS tokens are declared on :root in both stylesheets."""
    dark_path = os.path.join(PROJECT_ROOT, "assets", "style_dark.css")
    light_path = os.path.join(PROJECT_ROOT, "assets", "style_light.css")

    with open(dark_path, "r", encoding="utf-8") as f:
        dark_css = f.read()
    with open(light_path, "r", encoding="utf-8") as f:
        light_css = f.read()

    required_tokens = [
        "--bg-canvas",
        "--bg-surface",
        "--border-subtle",
        "--text-primary",
        "--stage-intro",
        "--stage-mature",
        "--delta-positive",
        "--delta-negative",
    ]

    for token in required_tokens:
        assert token in dark_css, f"Missing {token} in style_dark.css"
        assert token in light_css, f"Missing {token} in style_light.css"


def test_theme_user_preference_persistence(db_conn):
    """Verify that theme preference persists correctly in user_preferences table."""
    import db
    db.ensure_app_tables()

    # Save dark theme preference for test user
    db.save_user_pref("test_admin", "app", {"theme": "dark"})
    saved = db.load_user_prefs("test_admin", "app")
    assert saved is not None
    assert saved.get("theme") == "dark"

    # Toggle to light theme
    db.save_user_pref("test_admin", "app", {"theme": "light"})
    updated = db.load_user_prefs("test_admin", "app")
    assert updated.get("theme") == "light"
