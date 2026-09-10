"""Bounded, read-only Gemini API reviewer for committed planning snapshots.

The reviewer receives a git snapshot selected by SHA. It cannot edit the
repository, execute commands, or publish evidence. Publication remains a
separate Codex-controlled step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_FILES = (
    "docs/operations/CONTEXT_PACK.md",
    "docs/operations/INDEPENDENT_REVIEW_HARNESS_SPEC.md",
    "docs/planning/FDI_ADOPTION_MATRIX.md",
    ".planning/phases/12-explainable-grounded-orchestration/12-01-PLAN.md",
    "docs/CAPABILITY_STATUS.md",
)


def git_show(sha: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def snapshot(sha: str, paths: tuple[str, ...]) -> tuple[str, dict[str, str]]:
    subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], check=True)
    files = {path: git_show(sha, path) for path in paths}
    payload = json.dumps(files, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest(), files


def build_prompt(instructions: str, sha: str, snapshot_hash: str, files: dict[str, str]) -> str:
    sections = "\n\n".join(f"===== {path} =====\n{content}" for path, content in files.items())
    return (
        f"You are a bounded adversarial reviewer. Review only candidate SHA {sha}.\n"
        f"Snapshot SHA-256: {snapshot_hash}.\n"
        "Do not propose or execute code changes. Do not claim facts outside the snapshot.\n"
        "Return the requested structured verdict and concrete evidence.\n\n"
        f"REVIEW INSTRUCTIONS:\n{instructions}\n\nREPOSITORY SNAPSHOT:\n{sections}"
    )


def call_gemini(prompt: str, model: str) -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured")
    body = json.dumps({"contents": [{"role": "user", "parts": [{"text": prompt}]}]}).encode()
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=body,
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {detail[:1000]}") from exc
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini API response lacked a text candidate") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    instructions = args.prompt_file.read_text(encoding="utf-8")
    digest, files = snapshot(args.candidate, DEFAULT_FILES)
    prompt = build_prompt(instructions, args.candidate, digest, files)
    if args.dry_run:
        print(json.dumps({"candidate": args.candidate, "snapshot_sha256": digest, "files": list(files)}))
        return 0

    response = call_gemini(prompt, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "candidate_sha": args.candidate,
                "model": args.model,
                "snapshot_sha256": digest,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "response": response,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
