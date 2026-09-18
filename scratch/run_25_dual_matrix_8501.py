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

def atomic_save(results: list[dict]):
    tmp = OUT / "results.json.tmp"
    tmp.write_text(json.dumps(results, indent=2), encoding="utf-8")
    tmp.replace(OUT / "results.json")

def wait_for_rerun(page, timeout=20000):
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="attached", timeout=1000)
    except Exception:
        pass
    page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=timeout)

def login(page, user: str) -> None:
    page.goto(BASE_URL, wait_until="networkidle", timeout=45000)
    page.locator('input[type="text"]').first.wait_for(state="visible", timeout=30000)
    page.locator('input[type="text"]').first.fill(user)
    page.locator('input[type="password"]').first.fill(PASSWORD)
    page.locator('button:has-text("Sign In"), button:has-text("Login")').first.click()
    wait_for_rerun(page)
    page.wait_for_selector("section[data-testid='stSidebar']", state="visible", timeout=30000)
    
    # Reacquire elements after rerun
    more = page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"more", re.I)).first
    try:
        if more.is_visible(timeout=2000):
            more.click()
            wait_for_rerun(page)
    except Exception:
        pass

def open_page(page, label: str) -> None:
    link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile(label, re.I)).first
    link.wait_for(state="visible", timeout=15000)
    link.click()
    wait_for_rerun(page)

def ensure_theme(page, target_theme: str) -> None:
    if target_theme.lower() == "dark":
        btn_moon = page.locator("button").filter(has_text="🌙").first
        if btn_moon.is_visible(timeout=3000):
            btn_moon.click()
            wait_for_rerun(page)
            page.locator("button").filter(has_text="☀️").first.wait_for(state="visible", timeout=10000)
    else:
        btn_sun = page.locator("button").filter(has_text="☀️").first
        if btn_sun.is_visible(timeout=3000):
            btn_sun.click()
            wait_for_rerun(page)
            page.locator("button").filter(has_text="🌙").first.wait_for(state="visible", timeout=10000)

def run_user(browser, user: str, role: str, theme: str, results: list[dict]) -> None:
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100})
    page = ctx.new_page()
    try:
        login(page, user)
        ensure_theme(page, theme)
        open_page(page, "Stata Studio")
        
        for name, stata, _ in COMMANDS:
            started = time.time()
            text = ""
            status = "FAIL"
            detail = "Unknown error"
            try:
                inp = page.locator("input[aria-label='Stata Command Prompt:']").first
                inp.wait_for(state="visible", timeout=20000)
                inp.fill(stata)
                
                before_cards = page.locator(".stata-rich-terminal-card").count()
                page.get_by_role("button", name="Run Command").first.click()
                wait_for_rerun(page, timeout=30000)
                
                # Check what was rendered
                new_cards = page.locator(".stata-rich-terminal-card").count()
                if new_cards > before_cards:
                    card = page.locator(".stata-rich-terminal-card").last
                elif page.locator('[data-testid="stException"]').count() > 0:
                    card = page.locator('[data-testid="stException"]').last
                elif page.locator('[data-testid="stAlert"]').count() > 0:
                    card = page.locator('[data-testid="stAlert"]').last
                else:
                    card = page.locator(".stata-rich-terminal-card").last
                
                # Retry loop by reacquiring element inner text
                for attempt in range(3):
                    try:
                        text = card.inner_text()
                        status, detail = safe_status(text)
                        page.screenshot(path=str(OUT / f"{user}_{theme.lower()}_stata_{name}.png"), full_page=True)
                        break
                    except Exception as e:
                        if attempt == 2:
                            raise e
                        page.wait_for_timeout(1000)  # Reacquire delay
            except Exception as exc:
                status, detail, text = "FAIL", f"UI exception: {type(exc).__name__}: {exc}", ""
            
            results.append({"user": user, "role": role, "theme": theme, "interface": "Stata Studio", "command": name, "input": stata, "status": status, "detail": detail, "elapsed_s": round(time.time() - started, 2), "output_excerpt": text[:500]})
            atomic_save(results)

        if "--stata-only" in sys.argv:
            return

        open_page(page, "AI Assistant")
        chat = page.locator('textarea[aria-label="Ask ProfSur AI..."], textarea').first
        chat.wait_for(state="visible", timeout=20000)
        
        for name, _, prompt in COMMANDS:
            started = time.time()
            text = ""
            status = "FAIL"
            detail = "Unknown error"
            try:
                before = page.locator("[data-testid='stChatMessage']").count()
                chat.fill(prompt)
                page.keyboard.press("Enter")
                wait_for_rerun(page, timeout=45000)
                
                # Double check wait condition with correct keyword format
                try:
                    page.wait_for_function(
                        "([n]) => document.querySelectorAll('[data-testid=\"stChatMessage\"]').length > n",
                        arg=[before],
                        timeout=5000
                    )
                except Exception:
                    pass
                
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
                        page.wait_for_timeout(1000)
            except Exception as exc:
                status, detail, text = "FAIL", f"UI exception: {type(exc).__name__}: {exc}", ""
            
            results.append({"user": user, "role": role, "theme": theme, "interface": "AI Chatbot", "command": name, "input": prompt, "status": status, "detail": detail, "elapsed_s": round(time.time() - started, 2), "output_excerpt": text[:500]})
            atomic_save(results)
    finally:
        ctx.close()

def main() -> None:
    if not PASSWORD:
        raise SystemExit("Set PROFSUR_VERIFY_PASSWORD in the process environment.")
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for theme in ["Light", "Dark"]:
            for user, role in USERS:
                print(f"START {user} ({theme})", flush=True)
                run_user(browser, user, role, theme, results)
                print(f"DONE {user} ({theme})", flush=True)
        browser.close()
    
    counts = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print(json.dumps({"total": len(results), "counts": counts}, indent=2), flush=True)

if __name__ == "__main__":
    main()
