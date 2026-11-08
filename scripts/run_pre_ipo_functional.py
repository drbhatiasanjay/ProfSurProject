"""Prepare/run the real app with disposable storage, then invoke Playwright CLI.

No app imports. No original secrets copied. Browser execution is opt-in.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "tests/functional/pre_ipo"
PROFILES = {"profsurkumar": "researcher", "skumar": "researcher", "drbhatia": "admin", "sbhatia": "viewer", "e2e_new_researcher": "researcher"}
EXCLUDED = {".git", ".venv", "venv", "node_modules", "scratch", "paper", "tests", "graphify-out", "HndstnCocacola", "PreIPO_Documents"}


def contained(path: Path, parent: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(parent.resolve()) or resolved == parent.resolve():
        raise ValueError("Target must be strictly inside the disposable run directory")
    return resolved


def snapshot(source: Path, target: Path) -> list[dict]:
    """Copy source/config assets, never credentials, databases or downloaded evidence."""
    names = subprocess.check_output(["git", "-C", str(source), "ls-files", "-z"], text=True).split("\0")
    # Active implementation can contain not-yet-tracked source and migration files.
    names += subprocess.check_output(["git", "-C", str(source), "ls-files", "--others", "--exclude-standard", "-z"], text=True).split("\0")
    hashes = []
    for name in sorted(set(names)):
        rel = Path(name)
        if not name or any(p in EXCLUDED for p in rel.parts) or "secret" in rel.name.lower() or rel.is_absolute() or ".." in rel.parts:
            continue
        if rel.suffix.lower() not in {".py", ".sql", ".css", ".html", ".js", ".json", ".toml", ".csv", ".txt", ".md", ".svg", ".png", ".woff", ".woff2", ".ttf", ".yml", ".yaml"} and rel.name != "VERSION":
            continue
        original = source / rel
        if not original.is_file() or original.is_symlink():
            continue
        data = original.read_bytes()
        dest = contained(target / rel, target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        hashes.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(), "changed_during_copy": data != original.read_bytes()})
    if not (target / "app.py").exists():
        raise ValueError("Selected checkout is not ProfSurProject with canonical app.py")
    return hashes


def prepare(source: Path, dataset_db: Path | None = None) -> dict:
    import bcrypt
    run_dir = Path(tempfile.mkdtemp(prefix="profsur-functional-" )).resolve()
    app = run_dir / "app"
    app.mkdir()
    hashes = snapshot(source, app)
    if any(row["changed_during_copy"] for row in hashes):
        raise RuntimeError("Source changed during snapshot; wait for Antigravity to finish and retry")
    database = contained(run_dir / "disposable.sqlite", run_dir)
    if dataset_db:
        # Online backup is read-only at source. Scrub private/auth records in COPY only.
        with sqlite3.connect(dataset_db.resolve().as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(database) as dst:
            src.backup(dst)
            for (table,) in dst.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                if table.startswith(("pre_ipo_", "auth_")):
                    dst.execute('DELETE FROM "' + table.replace('"', '""') + '"')
            dst.commit()
    else:
        sqlite3.connect(database).close()
    account_data, lines = {}, []
    for username, role in PROFILES.items():
        password = secrets.token_urlsafe(24)
        account_data[username] = {"username": username, "password": password, "role": role}
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        lines += [f'[credentials.usernames.{username}]', f'email = "{username}@example.invalid"',
                  f'name = "Functional Test {username}"', f'password = "{hashed}"', f'role = "{role}"', '']
    secret = contained(app / ".streamlit/secrets.toml", app)
    secret.parent.mkdir(exist_ok=True)
    secret.write_text("\n".join(lines), encoding="utf-8")
    private = run_dir / "private-accounts.json"
    private.write_text(json.dumps(account_data), encoding="utf-8")
    private.chmod(0o600)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    fixtures = run_dir / "fixtures"
    subprocess.run([sys.executable, str(SUITE / "support/make_fixtures.py"), str(fixtures)], check=True)
    state = {"marker": "PROFSUR_DISPOSABLE_E2E_V1", "runId": run_dir.name.removeprefix("profsur-functional-"),
             "runDir": str(run_dir), "appRoot": str(app), "dbPath": str(database), "suiteRoot": str(SUITE),
             "python": sys.executable, "credentialsFile": str(private), "fixtureDir": str(fixtures),
             "sourceRoot": str(source), "baseURL": f"http://127.0.0.1:{port}", "port": port,
             "sourceHead": subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
             "preparedAt": datetime.now(timezone.utc).isoformat()}
    (run_dir / "source-manifest.json").write_text(json.dumps(hashes, indent=2), encoding="utf-8")
    (run_dir / "session.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def restart(state: dict, process, log):
    if process:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    env = os.environ.copy()
    for key in list(env):
        if any(token in key.upper() for token in ("API_KEY", "AUTH_USERS", "AUTH_TEST", "CMIE_PASSWORD")):
            env.pop(key, None)
    env.update(PROFSUR_DB_PATH=state["dbPath"], APP_ENV="test", ENABLE_CMIE="false", PYTHONUTF8="1")
    proc = subprocess.Popen([state["python"], "-m", "streamlit", "run", "app.py", "--server.port", str(state["port"]),
        "--server.address", "127.0.0.1", "--server.headless", "true", "--server.fileWatcherType", "none"],
        cwd=state["appRoot"], env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError("Isolated app exited; inspect server.log (not a UI acceptance result)")
        try:
            with urllib.request.urlopen(state["baseURL"] + "/_stcore/health", timeout=1) as response:
                if response.status == 200:
                    return proc
        except OSError:
            time.sleep(.25)
    proc.terminate()
    raise RuntimeError("Isolated app startup timed out")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, default=ROOT)
    parser.add_argument("--dataset-db", type=Path, help="Optional read-only baseline copy for global panel navigation; private/auth tables scrubbed in copy")
    parser.add_argument("--execute", action="store_true", help="Actually start app and run browsers; default only prepares")
    parser.add_argument("--corpus", action="store_true")
    parser.add_argument("--gold-plan", type=Path)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("playwright_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    source = args.app_root.resolve()
    if source.name != "ProfSurProject":
        parser.error("Only ProfSurProject is allowed")
    if args.corpus and not args.gold_plan:
        parser.error("Corpus execution requires --gold-plan with independently verified expectations")
    state = prepare(source, args.dataset_db)
    print(json.dumps({"session": str(Path(state["runDir"]) / "session.json"), "sourceHead": state["sourceHead"],
                      "mode": "EXECUTE" if args.execute else "PREPARED_ONLY", "note": "No browser pass claimed until execution"}))
    if not args.execute:
        return
    cli = SUITE / "node_modules/@playwright/test/cli.js"
    if not cli.exists():
        raise SystemExit("BLOCKED: Install suite dependencies and Chromium using README before execution")
    env = os.environ.copy()
    env.update(PROFSUR_E2E_SESSION=str(Path(state["runDir"]) / "session.json"), PROFSUR_E2E_CORPUS="1" if args.corpus else "0")
    if args.gold_plan:
        env["PROFSUR_E2E_GOLD_PLAN"] = str(args.gold_plan.resolve())
    extra = args.playwright_args[1:] if args.playwright_args[:1] == ["--"] else args.playwright_args
    command = [shutil.which("node") or "node", str(cli), "test", *extra]
    if not args.headed:
        env["PROFSUR_E2E_HEADLESS"] = "1"
    proc = None
    with open(Path(state["runDir"]) / "server.log", "ab") as log:
        try:
            proc = restart(state, None, log)
            # Dedicated local control channel can restart only this owned process.
            from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
            import threading
            token = secrets.token_urlsafe(24)
            class Control(BaseHTTPRequestHandler):
                def do_POST(self):
                    nonlocal proc
                    if self.path != "/restart" or self.headers.get("Authorization") != token:
                        self.send_error(403)
                        return
                    try:
                        proc = restart(state, proc, log)
                        self.send_response(200)
                        self.end_headers()
                    except Exception:
                        self.send_error(500, "Isolated restart failed")
                def log_message(self, *unused):
                    pass
            server = ThreadingHTTPServer(("127.0.0.1", 0), Control)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            # Token remains runtime-only; never attach this private file to reports.
            control = Path(state["runDir"]) / "private-control.json"
            control.write_text(json.dumps({"url": f"http://127.0.0.1:{server.server_port}/restart", "token": token}))
            env["PROFSUR_E2E_CONTROL"] = str(control)
            try:
                completed = subprocess.run(command, cwd=SUITE, env=env)
            finally:
                server.shutdown()
            return completed.returncode
        finally:
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()


if __name__ == "__main__":
    sys.exit(main() or 0)
