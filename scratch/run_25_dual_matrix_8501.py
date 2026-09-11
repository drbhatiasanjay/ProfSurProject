"""Authenticated 25-command dual-interface matrix for the canonical 8501 app."""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8501"
OUT = Path("scratch/dual_25_matrix_8501")
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = os.environ.get("PROFSUR_VERIFY_PASSWORD", "")
USERS = [("profsurkumar", "researcher"), ("skumar", "researcher"), ("drbhatia", "admin"), ("sbhatia", "viewer")]

COMMANDS = [
    ("regress", "regress leverage prof profit_margin", "Run pooled OLS regression of leverage on profitability and profit_margin (which is perfectly collinear)."),
    ("xtreg", "xtreg leverage prof, fe", "Run fixed effects panel regression of leverage on profitability, assuming no panel is set."),
    ("ivregress", "ivregress 2sls leverage (prof = ) size", "Run an instrumental variable regression for leverage with prof as endogenous, but leave instruments empty."),
    ("hdfe", "hdfe leverage prof, absorb(non_existent_var)", "Prove profitability causes lower leverage using hdfe absorbing a nonexistent variable."),
    ("gmm", "gmm leverage prof tang, lags(1 30)", "Run a dynamic panel GMM using lags 1 to 30 as instruments."),
    ("didregress", "didregress leverage prof", "Run a Difference-in-Differences regression of leverage on profitability."),
    ("summarize", "summarize company_name, detail", "Give me detailed summary statistics for the string column company_name."),
    ("tabstat", "tabstat leverage, by(prof)", "Create group tabulations of leverage grouped by the continuous variable profitability."),
    ("tabulate", "tabulate prof", "Show me frequency tables for the continuous variable profitability."),
    ("pwcorr", "pwcorr prof, star(0.05)", "Calculate a correlation matrix for just profitability."),
    ("hausman", "hausman fe re", "Run a Hausman test to compare FE and RE models."),
    ("estat_vif", "estat vif", "Calculate Variance Inflation Factors."),
    ("estimates_store", "estimates store m1", "Store the current model results as m1."),
    ("esttab", "esttab m1 m2", "Display side-by-side tables for models m1 and m2."),
    ("xttest0", "xttest0", "Run the Breusch-Pagan LM test."),
    ("xtserial", "xtserial", "Run the Wooldridge test for autocorrelation."),
    ("test", "test prof = size", "Perform a Wald test that profitability equals size."),
    ("predict", "predict res, resid", "Generate predicted residuals."),
    ("scatter", "scatter leverage prof tang size", "Create a scatter plot with leverage, profitability, tangibility, and size."),
    ("histogram", "histogram company_code", "Show a histogram of the company_code ID variable."),
    ("graph_box", "graph box leverage, over(prof)", "Create a box plot of leverage grouped over profitability."),
    ("coefplot", "coefplot", "Plot the coefficients."),
    ("margins", "margins", "Calculate marginal effects."),
    ("predict_ml", "predict_ml leverage prof", "Run a Random Forest to predict leverage using profitability."),
    ("scenario", "scenario leverage prof interventions(prof = prof * 1.1) prof = prof * 1.2", "Simulate a scenario where both inline and intervention options conflict."),
]


def safe_status(text: str) -> tuple[str, str]:
    lowered = text.lower()
    fatal = any(token in lowered for token in ("traceback", "modulenotfounderror", "importerror", "connectionerror"))
    typed = any(token in lowered for token in ("r(", "error", "unsupported", "invalid", "not found", "requires", "syntax"))
    if fatal:
        return "FAIL", "fatal runtime/provider error"
    if typed:
        return "PASS_FAIL_CLOSED", "typed/user-visible rejection"
    return "PASS", "result rendered"


def login(page, user: str) -> None:
    page.goto(BASE_URL, wait_until="networkidle", timeout=45000)
    page.locator('input[type="text"]').first.wait_for(state="visible", timeout=30000)
    page.locator('input[type="text"]').first.fill(user)
    page.locator('input[type="password"]').first.fill(PASSWORD)
    page.locator('button:has-text("Sign In"), button:has-text("Login")').first.click()
    page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
    time.sleep(2)
    more = page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"more", re.I)).first
    try:
        if more.is_visible(timeout=3000):
            more.click()
            time.sleep(1)
    except Exception:
        pass


def open_page(page, label: str) -> None:
    link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile(label, re.I)).first
    link.wait_for(state="visible", timeout=15000)
    link.click()
    time.sleep(3)


def ensure_theme(page, target_theme: str) -> None:
    time.sleep(1) # wait for render
    if target_theme.lower() == "dark":
        btn_moon = page.locator("button").filter(has_text="🌙").first
        if btn_moon.is_visible(timeout=3000):
            btn_moon.click()
            page.locator("button").filter(has_text="☀️").first.wait_for(state="visible", timeout=10000)
            time.sleep(1)
    else:
        btn_sun = page.locator("button").filter(has_text="☀️").first
        if btn_sun.is_visible(timeout=3000):
            btn_sun.click()
            page.locator("button").filter(has_text="🌙").first.wait_for(state="visible", timeout=10000)
            time.sleep(1)

def run_user(browser, user: str, role: str, theme: str) -> list[dict]:
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100})
    page = ctx.new_page()
    rows = []
    try:
        login(page, user)
        ensure_theme(page, theme)
        open_page(page, "Stata Studio")
        for name, stata, _ in COMMANDS:
            started = time.time()
            text = ""
            try:
                inp = page.locator("input[aria-label='Stata Command Prompt:']").first
                inp.wait_for(state="visible", timeout=20000)
                inp.fill(stata)
                
                # Prevent stale result cards
                before_cards = page.locator(".stata-rich-terminal-card").count()
                page.get_by_role("button", name="Run Command").first.click()
                
                page.wait_for_function("(n) => document.querySelectorAll('.stata-rich-terminal-card').length > n", arg=before_cards, timeout=20000)
                card = page.locator(".stata-rich-terminal-card").last
                card.wait_for(state="visible", timeout=20000)
                
                # Retry for detached elements
                for attempt in range(3):
                    try:
                        time.sleep(1)
                        text = card.inner_text()
                        status, detail = safe_status(text)
                        page.screenshot(path=str(OUT / f"{user}_{theme.lower()}_stata_{name}.png"), full_page=True)
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        time.sleep(1)
            except Exception as exc:
                status, detail, text = "FAIL", f"UI exception: {type(exc).__name__}: {exc}", ""
            rows.append({"user": user, "role": role, "theme": theme, "interface": "Stata Studio", "command": name, "input": stata, "status": status, "detail": detail, "elapsed_s": round(time.time() - started, 2), "output_excerpt": text[:500]})

        if "--stata-only" in sys.argv:
            return rows

        open_page(page, "AI Assistant")
        chat = page.locator('textarea[aria-label="Ask ProfSur AI..."], textarea').first
        chat.wait_for(state="visible", timeout=20000)
        for name, _, prompt in COMMANDS:
            started = time.time()
            text = ""
            try:
                before = page.locator("[data-testid='stChatMessage']").count()
                chat.fill(prompt)
                page.keyboard.press("Enter")
                page.wait_for_function("(n) => document.querySelectorAll('[data-testid=stChatMessage]').length > n", arg=before, timeout=45000)
                time.sleep(3)
                
                messages = page.locator("[data-testid='stChatMessage']")
                for attempt in range(3):
                    try:
                        text = messages.last.inner_text()
                        status, detail = safe_status(text)
                        page.screenshot(path=str(OUT / f"{user}_{theme.lower()}_ai_{name}.png"), full_page=True)
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        time.sleep(1)
            except Exception as exc:
                status, detail, text = "FAIL", f"UI exception: {type(exc).__name__}: {exc}", ""
            rows.append({"user": user, "role": role, "theme": theme, "interface": "AI Chatbot", "command": name, "input": prompt, "status": status, "detail": detail, "elapsed_s": round(time.time() - started, 2), "output_excerpt": text[:500]})
    finally:
        ctx.close()
    return rows


def main() -> None:
    if not PASSWORD:
        raise SystemExit("Set PROFSUR_VERIFY_PASSWORD in the process environment.")
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for theme in ["Light", "Dark"]:
            for user, role in USERS:
                print(f"START {user} ({theme})", flush=True)
                results.extend(run_user(browser, user, role, theme))
                print(f"DONE {user} ({theme})", flush=True)
        browser.close()
    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    counts = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"total": len(results), "counts": counts}, indent=2), flush=True)


if __name__ == "__main__":
    main()
