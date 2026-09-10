"""Regression contract for experimental Streamlit page path resolution."""

from pathlib import Path


def test_experimental_wrapper_resolves_overview_from_repository_root():
    project_root = Path(__file__).resolve().parents[1]
    page = (project_root / "pages" / "0_overview.py").resolve()
    assert page.is_file()
    assert page.parent == project_root / "pages"
