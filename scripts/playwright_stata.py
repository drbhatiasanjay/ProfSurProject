"""Reusable Playwright helpers for authenticated Stata Studio verification."""

from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


def authenticate(page: Page, base_url: str, username: str, password: str) -> None:
    page.goto(base_url, wait_until="networkidle", timeout=60_000)
    login = page.get_by_role("button", name=re.compile(r"(?:login|sign in)", re.I)).first
    if login.count() and login.is_visible():
        page.get_by_label("Username or email").fill(username)
        page.get_by_role("textbox", name="Password").fill(password)
        login.click()
        page.wait_for_timeout(3_000)


def open_stata_studio(page: Page, base_url: str) -> None:
    page.goto(f"{base_url}/stata_studio", wait_until="networkidle", timeout=60_000)
    page.wait_for_function(
        "() => document.body.innerText.includes('Stata Studio')", timeout=20_000
    )


def submit_stata_command(
    page: Page,
    base_url: str,
    command: str,
    fragments: list[str | tuple[str, ...]],
    *,
    fresh: bool = True,
    evidence_dir: Path | None = None,
) -> str:
    if fresh:
        open_stata_studio(page, base_url)
    command_input = page.locator('input[aria-label="Stata Command Prompt:"]').first
    command_input.fill(command)
    page.get_by_role("button", name=re.compile("Run Command", re.I)).first.click()
    expected = [f"Stata 18 SE · {command}", *fragments]
    try:
        page.wait_for_function(
            "parts => parts.every(part => {"
            "const choices = Array.isArray(part) ? part : [part];"
            "return choices.some(choice => document.body.innerText.toLowerCase().includes(choice.toLowerCase()));"
            "})",
            arg=expected,
            timeout=30_000,
        )
    except PlaywrightTimeoutError:
        if evidence_dir:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^a-z0-9]+", "_", command.lower()).strip("_")
            (evidence_dir / f"debug_{safe_name}.txt").write_text(
                page.inner_text("body"), encoding="utf-8"
            )
            page.screenshot(path=str(evidence_dir / f"debug_{safe_name}.png"), full_page=True)
        raise
    return page.inner_text("body")
