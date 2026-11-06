"""Reusable E2E Playwright Authentication & Navigation Helper.

Designed to prevent selector timeouts, correctly navigate Streamlit's radio-first
input hierarchy, and provide deterministic authentication and screen verification.
"""

import asyncio
from typing import Optional


async def wait_for_streamlit_ready(page, timeout_ms: int = 15000) -> bool:
    """Wait until Streamlit finishes its initial script run and spinners clear."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
        # Check if spinner/status widget is running
        spinner = page.locator("[data-testid='stStatusWidget']")
        if await spinner.count() > 0:
            await spinner.wait_for(state="detached", timeout=timeout_ms)
        return True
    except Exception:
        return False


async def authenticate_session(
    page,
    username: str,
    password: str,
    base_url: str = "http://localhost:8501",
    timeout_ms: int = 20000,
) -> bool:
    """Authenticate a Streamlit session reliably.
    
    Avoids generic locator("input") which matches Streamlit's hidden radio buttons.
    Uses explicit input[type='text'] and input[type='password'].
    """
    await page.goto(base_url, timeout=timeout_ms)
    await page.wait_for_load_state("domcontentloaded")
    
    # Check if already authenticated
    sign_out_btn = page.locator("button:has-text('Sign Out'), button:has-text('Logout')")
    if await sign_out_btn.count() > 0:
        return True

    # Specifically target text and password inputs
    user_input = page.locator("input[type='text']").first
    pwd_input = page.locator("input[type='password']").first

    await user_input.wait_for(state="visible", timeout=timeout_ms)
    await user_input.fill(username)
    await pwd_input.fill(password)

    # Click Sign In button
    submit_btn = page.locator(
        "button:has-text('Sign In'), button:has-text('Log In'), button:has-text('Login')"
    ).first
    await submit_btn.click()

    # Wait for post-login indicator
    try:
        await page.wait_for_selector(
            "button:has-text('Sign Out'), button:has-text('Logout'), [data-testid='stSidebarNav']",
            timeout=timeout_ms,
        )
        await page.wait_for_timeout(1000)  # Short debounce for rerun
        return True
    except Exception as exc:
        print(f"[Auth Error] Failed to verify login for {username}: {exc}")
        return False


async def toggle_theme(page, target_theme: str = "dark") -> bool:
    """Toggle theme between light and dark if theme button exists."""
    theme_btn = page.locator(
        "button:has-text('🌙'), button:has-text('☀️'), button[title*='theme' i]"
    )
    if await theme_btn.count() > 0:
        await theme_btn.first.click()
        await page.wait_for_timeout(1200)
        return True
    return False
