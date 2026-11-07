"""Minimal cloud connectivity probe; never prints credentials or request URLs."""
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import os
    from google import genai
    from google.genai import types
    secrets = tomllib.loads((ROOT / ".streamlit/secrets.toml").read_text(encoding="utf-8-sig"))
    key = (secrets.get("GEMINI_API_KEY") or secrets.get("GOOGLE_API_KEY")
           or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
           or secrets.get("credentials", {}).get("gemini_api_key"))
    if not key:
        print(json.dumps({"configured": False}))
        return 1
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000))
    model = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.1-flash-lite"
    try:
        response = client.models.generate_content(model=model, contents="Reply with OK only.",
                                                  config=types.GenerateContentConfig(max_output_tokens=64))
        print(json.dumps({"configured": True, "model": model, "connected": True,
                          "returned_text": bool(response.text)}))
        return 0
    except Exception as exc:
        print(json.dumps({"configured": True, "model": model, "connected": False,
                          "error_type": type(exc).__name__, "status": getattr(exc, "code", None)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
