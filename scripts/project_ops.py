#!/usr/bin/env python3
"""
project_ops.py — Unified Project Operations CLI for LifeCycle Leverage Dashboard

Provides zero-bloat, token-efficient command wrappers for:
- status: Check local/remote git sync, GitHub Actions CI/CD run, and Cloud Run revision.
- test: Quiet test runner that prevents multi-thousand token terminal dumps.
- push: Keyring-isolated git pre-push test and commit/push.
- verify: Headless Playwright browser verification for local or live GCP.
"""

import sys
import os
import argparse
import subprocess
import json
import asyncio
import shutil
import tempfile
import time
from pathlib import Path

def _get_clean_env():
    env = os.environ.copy()
    env.pop("GITHUB_TOKEN", None)  # Prevent invalid token override of gh keyring
    return env

def cmd_status(args):
    print("=== GIT STATUS ===")
    res_local = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    local_sha = res_local.stdout.strip()
    print(f"Local HEAD:  {local_sha}")

    res_remote = subprocess.run(["git", "rev-parse", "@{upstream}"], capture_output=True, text=True)
    remote_sha = res_remote.stdout.strip() if res_remote.returncode == 0 else "no upstream"
    print(f"Upstream HEAD: {remote_sha}")
    if local_sha == remote_sha:
        print("Status:      IN SYNC (100% Up-to-date)")
    else:
        print("Status:      OUT OF SYNC (Push required)")

    print("\n=== CI/CD WORKFLOW (GitHub Actions) ===")
    env = _get_clean_env()
    cmd = ["gh", "run", "list", "--limit", "1", "--json", "databaseId,status,conclusion,name,headSha,updatedAt"]
    res_gh = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res_gh.returncode == 0:
        runs = json.loads(res_gh.stdout)
        if runs:
            r = runs[0]
            print(f"Run ID:      {r.get('databaseId')}")
            print(f"Workflow:    {r.get('name')}")
            print(f"Status:      {r.get('status')} | Conclusion: {r.get('conclusion')}")
            print(f"Commit:      {r.get('headSha')}")
            print(f"Updated:     {r.get('updatedAt')}")
    else:
        print("Could not query GitHub Actions:", res_gh.stderr.strip())

def cmd_test(args):
    print("=== RUNNING TESTS (Quiet Mode) ===")
    started = time.perf_counter()
    tier = "fast" if args.fast else args.tier
    env = _get_clean_env()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    with tempfile.TemporaryDirectory(prefix="profsur-tests-") as temp_dir:
        test_db = os.path.join(temp_dir, "capital_structure.db")
        shutil.copy2("capital_structure.db", test_db)
        env["PROFSUR_DB_PATH"] = test_db
        if tier == "fast":
            cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/test_fast.ps1"]
        elif tier == "targeted":
            cmd = [
                sys.executable, "-m", "pytest", "-q", "--tb=line",
                "tests/test_wave5_independent_review_repair.py",
                "tests/test_wave5_contract_red.py", "tests/test_wave5_numerical_golden.py",
                "tests/test_wave2_abstraction.py", "tests/test_wave4_expansion.py",
                "tests/test_analysis_run_contracts.py", "tests/test_model_result_context.py",
                "tests/test_stata_bidirectional_nlp.py", "tests/test_stata_studio_widgets.py",
                "tests/test_llm_adapter_import_safety.py", "tests/test_capability_status_contract.py",
                "tests/test_command_contract_docs.py", "tests/test_automation_contracts.py",
                "--basetemp", os.path.join(temp_dir, "pytest"),
            ]
        else:
            cmd = [
                sys.executable, "-m", "pytest", "tests/",
                "--ignore=tests/smoke_auth.py", "--ignore=tests/smoke_phase1.py",
                "-q", "--tb=line",
                "--basetemp", os.path.join(temp_dir, "pytest"),
            ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    elapsed = round(time.perf_counter() - started, 3)
    output_lines = res.stdout.strip().splitlines()
    summary = output_lines[-1] if output_lines else "No test output"
    print(f"Tier:    {tier}")
    print(f"Summary: {summary}")
    print(f"Elapsed: {elapsed:.3f}s")
    if args.evidence:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        evidence = {
            "commit": commit,
            "tier": tier,
            "returncode": res.returncode,
            "summary": summary,
            "elapsed_seconds": elapsed,
            "command": cmd,
        }
        path = Path(args.evidence)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    if res.returncode != 0:
        print("\nFailures:")
        for line in output_lines:
            if "FAILED" in line or "ERROR" in line:
                print(f"  {line}")
        sys.exit(1)
    else:
        print("Result:  ALL TESTS PASSED")

def cmd_push(args):
    print("=== PUSHING TO GITHUB (pre-push hook enforces verification) ===")
    env = _get_clean_env()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    push_proc = subprocess.run(
        ["git", "push", "--set-upstream", "origin", branch], env=env, capture_output=True, text=True
    )
    if push_proc.returncode == 0:
        print(f"Successfully pushed {branch} to origin/{branch}.")
    else:
        print("Git push error:", push_proc.stderr)
        sys.exit(1)

async def _run_verify_async(target_url, username, password, out_img):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        print(f"Navigating to {target_url}...")
        await page.goto(target_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # Handle login if needed
        user_input = page.locator('input[aria-label="Username"], input[type="text"]').first
        pwd_input = page.locator('input[aria-label="Password"], input[type="password"]').first
        if await user_input.is_visible():
            if not password:
                raise RuntimeError("Set PROFSUR_VERIFY_PASSWORD or pass --password for authenticated verification.")
            await user_input.fill(username)
            await pwd_input.fill(password)
            await page.locator('button:has-text("Login"), button:has-text("Sign In")').first.click()
            await page.wait_for_timeout(3000)

        os.makedirs(os.path.dirname(os.path.abspath(out_img)), exist_ok=True)
        await page.screenshot(path=out_img)
        print(f"Verification screenshot saved to: {out_img}")
        await browser.close()

def cmd_verify(args):
    env = args.env
    url = "http://localhost:8501" if env == "local" else "https://lifecycle-leverage-779655496440.us-east1.run.app"
    out_img = f"scratch/verify_{env}_screen.png"
    print(f"=== VERIFYING {env.upper()} DEPLOYMENT ===")
    asyncio.run(_run_verify_async(url, args.user, args.password, out_img))

def main():
    parser = argparse.ArgumentParser(description="LifeCycle Leverage Project Ops CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Check local/remote sync and CI/CD status")
    p_status.set_defaults(func=cmd_status)

    # test
    p_test = subparsers.add_parser("test", help="Run tests with quiet token-efficient output")
    p_test.add_argument("--fast", action="store_true", help="Run targeted critical tests only")
    p_test.add_argument("--tier", choices=["fast", "targeted", "full"], default="targeted")
    p_test.add_argument("--evidence", help="Write machine-readable JSON test evidence")
    p_test.set_defaults(func=cmd_test)

    # push
    p_push = subparsers.add_parser("push", help="Run pre-push tests and push master to origin")
    p_push.set_defaults(func=cmd_push)

    # verify
    p_verify = subparsers.add_parser("verify", help="Run Playwright verification on local or GCP")
    p_verify.add_argument("--env", choices=["local", "gcp"], default="gcp", help="Target environment")
    p_verify.add_argument("--user", default="profsurkumar", help="Login username")
    p_verify.add_argument("--password", default=os.environ.get("PROFSUR_VERIFY_PASSWORD", ""), help="Login password")
    p_verify.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
