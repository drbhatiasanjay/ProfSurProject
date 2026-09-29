"""Apply two bounded repairs to the pinned V2 image without replacing its UI."""
from pathlib import Path
import ast
import re
import sys


def patch_scorecard(source):
    for name in ("_prof_sign", "_tang_sign"):
        old = f"{name} = v\n"
        if source.count(old) != 1:
            raise ValueError(f"Unexpected deployed scorecard shape: {name}")
        source = source.replace(old, f'{name} = v.get("coef") if isinstance(v, dict) else v\n')
    ast.parse(source)
    return source


def patch_chat(source):
    pattern = r'        _has_gemini_key = bool\(\n.*?\n        \)'
    source, count = re.subn(pattern, '        _has_gemini_key = bool(get_gemini_api_key())', source, flags=re.S)
    if count != 1 or source.count("import os\n") != 1:
        raise ValueError("Unexpected deployed chat configuration shape")
    source = source.replace("import os\n", "import os\nfrom models.runtime_config import get_gemini_api_key\n", 1)
    ast.parse(source)
    return source


def main(root):
    changes = {
        root / "pages/25_stata_studio_v2.py": patch_scorecard,
        root / "pages/19_ai_assistant.py": patch_chat,
    }
    patched = {path: patch(path.read_text(encoding="utf-8")) for path, patch in changes.items()}
    for path, source in patched.items():
        path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
