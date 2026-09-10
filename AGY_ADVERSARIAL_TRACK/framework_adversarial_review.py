import os
import sys
import toml
import requests
import json

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load secrets
secrets_path = os.path.join(PROJECT_ROOT, ".streamlit", "secrets.toml")
secrets = toml.load(secrets_path)
api_key = secrets.get("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY found.")
    sys.exit(1)

# Read context files
def read_file(filepath):
    with open(os.path.join(PROJECT_ROOT, filepath), "r", encoding="utf-8") as f:
        return f.read()

red_team_analysis = read_file("AGY_ADVERSARIAL_TRACK/RED_TEAM_ANALYSIS.md")
router_code = read_file("AGY_EXPERIMENTAL_TRACK/experimental_analytical_router.py")

# Construct the prompt
prompt = f"""
You are an independent Adversarial Reviewer. 
Antigravity just conducted a Red Team Analysis on our new Phase 15 performance optimizations.

Here is the NEW Experimental Code Antigravity wrote (with deep copy, thread locks, and idempotent guards):
```python
{router_code}
```

Here is Antigravity's Red Team Analysis:
```markdown
{red_team_analysis}
```

YOUR TASK:
Perform a PARALLEL ADVERSARIAL REVIEW. 
1. Do you agree with Antigravity's assessment? Are the enterprise mitigations (Redis, AST parser, Pre-execution) correct?
2. What OTHER hidden vulnerabilities exist in `optimized_analytical_router.py`? Look closely at concurrent access, memory leaks, or context desyncs.
3. Be brutally honest and output your findings in a GitHub-ready Markdown format.
"""

print("Running parallel adversarial review via Gemini (raw requests)...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}
data = {
    "contents": [{"parts": [{"text": prompt}]}]
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    output_path = os.path.join(PROJECT_ROOT, "AGY_ADVERSARIAL_TRACK", "CODEX_PARALLEL_REVIEW.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Review complete. Saved to: {output_path}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
