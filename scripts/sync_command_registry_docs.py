import sys, os
sys.path.insert(0, os.path.abspath('.'))
from models.stata_engine import COMMAND_REGISTRY

def generate_markdown():
    lines = [
        "# Stata Command Capabilities & Registry Specification",
        "",
        "**Auto-Generated Documentation Gate**",
        "Source: `models.stata_engine.COMMAND_REGISTRY`",
        "",
        "| Stata Command | Tier / Support Status | Handled Subcommands / Notes | Actionable Alternative / Guidance |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for cmd, info in sorted(COMMAND_REGISTRY.items()):
        tier = info.get("tier", "UNKNOWN")
        subcmds = ", ".join(info.get("subcommands", [])) if info.get("subcommands") else "-"
        alt = info.get("alternative", "-")
        lines.append(f"| `{cmd}` | **{tier}** | {subcmds} | {alt} |")
    
    lines.append("")
    lines.append("---")
    lines.append("*(This file is automatically synchronized from `models/stata_engine.py` by `scripts/sync_command_registry_docs.py`)*")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    doc_path = "docs/COMMAND_CAPABILITIES.md"
    content = generate_markdown()
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Synchronized Stata capabilities to {doc_path}")
