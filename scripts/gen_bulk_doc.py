#!/usr/bin/env python3
"""
gen_bulk_doc.py — Offload high-volume HTML/Markdown generation

Generates large repetitive documentation, tables, and HTML templates
without consuming Claude Pro reasoning tokens.
Supports:
1. Pure Python AST / Jinja2 / String template generation.
2. Fast low-cost generation via Gemini 1.5 Flash (via GEMINI_API_KEY / GOOGLE_API_KEY).
"""

import os
import sys
import argparse
import urllib.request
import json

def generate_via_template(template_name, output_file, context_data=None):
    """Generates standard boilerplate documentation from structured templates."""
    print(f"Generating {template_name} -> {output_file} via Python template engine...")
    header = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>LifeCycle Leverage Documentation</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0F172A; color: #F8FAFC; padding: 24px; }
        .card { background: #1E293B; border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid #334155; }
        h1, h2, h3 { color: #38BDF8; }
        code { background: #0B1120; padding: 2px 6px; border-radius: 4px; color: #F43F5E; font-size: 13px; }
    </style>
</head>
<body>
"""
    body = f"    <div class='card'>\n        <h1>LifeCycle Leverage Guide: {template_name}</h1>\n        <p>Generated automatically to preserve Pro token quota.</p>\n    </div>\n"
    footer = "</body>\n</html>"
    
    content = header + body + footer
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Template successfully written to {output_file} (0 Claude tokens consumed).")

def generate_via_gemini_flash(prompt, output_file, api_key=None):
    """Offloads massive text/HTML generation to Gemini 1.5 Flash."""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("Warning: No GEMINI_API_KEY found in environment. Falling back to template mode.")
        generate_via_template("Flash Document", output_file)
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Generated {len(text)} characters via Gemini Flash -> {output_file}")
    except Exception as e:
        print(f"Error calling Gemini Flash: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bulk Doc / HTML Generator")
    parser.add_argument("--template", default="academic_guide", help="Template name")
    parser.add_argument("--out", default="scratch/generated_guide.html", help="Output filepath")
    parser.add_argument("--prompt", help="Prompt for Gemini Flash offloading")
    args = parser.parse_args()

    if args.prompt:
        generate_via_gemini_flash(args.prompt, args.out)
    else:
        generate_via_template(args.template, args.out)

if __name__ == "__main__":
    main()
