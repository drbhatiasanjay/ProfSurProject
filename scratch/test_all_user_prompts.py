"""Provider matrix smoke harness for AI Assistant chart prompts.

Run with a live Streamlit server:
    py -3.12 -u scratch/test_all_user_prompts.py --backend gemini

Credentials are read from E2E_USERNAME/E2E_PASSWORD. The harness intentionally
uses a small acceptance set; the exhaustive PDF prompts can be supplied later
through --prompt-file when their schema expectations are normalized.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


PROMPTS = [
    ("TS-01", "Provide a table and a line graph showing average profitability (ROA) for each year from 2001 to 2024."),
    ("LC-01", "Show a bar chart and summary table comparing average leverage across life stages."),
    ("MC-01", "Plot average leverage and average profitability on the same chart across all years."),
    ("SC-03", "Create a scatter plot of firm size versus leverage for firms in 2024."),
    ("NL-01", "Visualise the evolution of corporate debt in India over the past 25 years."),
    ("ED-02", "Plot the average NDTS by life stage."),
]


def _chart_requested(prompt: str) -> bool:
    return any(word in prompt.lower() for word in (
        "chart", "graph", "plot", "visual", "bar", "trend", "illustrat", "diagram",
    ))


def _login(page, base: str, username: str, password: str) -> None:
    page.goto(base, wait_until="networkidle", timeout=90_000)
    page.locator('[data-testid="stTextInput"] input').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Login")').first.click()
    page.wait_for_timeout(8_000)
    if "continue to dashboard" in page.inner_text("body").lower():
        page.locator('button:has-text("Continue to Dashboard")').click()
        page.wait_for_timeout(5_000)


def _select_backend(page, backend: str) -> None:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    radio = sidebar.get_by_text(backend, exact=True).first
    radio.click(timeout=10_000)
    page.wait_for_timeout(2_000)


def _submit_prompt(page, prompt: str) -> tuple[bool, bool, str]:
    before = page.locator('[data-testid="stChatMessage"]').count()
    chat = page.locator('[data-testid="stChatInput"] textarea')
    chat.fill(prompt)
    chat.press("Enter")
    try:
        page.wait_for_function(
            "([selector, count]) => document.querySelectorAll(selector).length > count",
            ['[data-testid="stChatMessage"]', before],
            timeout=120_000,
        )
    except PlaywrightTimeoutError:
        return False, False, "timed out waiting for assistant response"
    page.wait_for_timeout(2_000)
    body = page.inner_text("body")
    response_exists = page.locator('[data-testid="stChatMessage"]').count() > before
    chart_exists = page.locator('[data-testid="stPlotlyChart"]').count() > 0
    error_markers = re.findall(r"\[(?:Gemini|Anthropic|Ollama) (?:error|backend)[^\]]*\]", body, re.I)
    return response_exists and not error_markers, chart_exists, "; ".join(error_markers)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.getenv("BASE", "http://localhost:8501"))
    parser.add_argument("--backend", choices=("gemini", "anthropic", "ollama"), action="append")
    parser.add_argument("--output", default="chart_prompt_results.json")
    args = parser.parse_args()
    username = os.getenv("E2E_USERNAME")
    password = os.getenv("E2E_PASSWORD")
    if not username or not password:
        raise SystemExit("Set E2E_USERNAME and E2E_PASSWORD before running the harness.")

    backends = args.backend or ["gemini", "anthropic", "ollama"]
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for backend in backends:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            try:
                _login(page, args.base, username, password)
                page.goto(f"{args.base}/ai_assistant", wait_until="networkidle", timeout=90_000)
                page.wait_for_timeout(4_000)
                _select_backend(page, backend)
                for test_id, prompt in PROMPTS:
                    started = time.time()
                    response_ok, chart_ok, error = _submit_prompt(page, prompt)
                    result = {
                        "test_id": test_id,
                        "backend": backend,
                        "response": response_ok,
                        "chart_expected": _chart_requested(prompt),
                        "chart": chart_ok,
                        "elapsed_s": round(time.time() - started, 1),
                        "error": error,
                    }
                    results.append(result)
                    print(json.dumps(result), flush=True)
            finally:
                page.close()
        browser.close()

    Path(args.output).write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [r for r in results if not r["response"] or (r["chart_expected"] and not r["chart"])]
    print(f"Completed {len(results)} checks; failures={len(failed)}; report={args.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
