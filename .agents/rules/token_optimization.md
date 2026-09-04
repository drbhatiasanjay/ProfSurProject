# Token Optimization & Context Engineering Rules

## 1. Ponytail Decision Ladder (Minimal Code Principle)
Before writing or proposing any new code, enforce this evaluation hierarchy:
1. **Necessity Filter:** Does this code/feature strictly need to exist to satisfy the user's explicit request?
2. **Reuse Existing:** Check `models/`, `utils/`, and `components/` first. Reuse existing functions instead of writing duplicates.
3. **Standard Library / Built-ins:** Prefer Python/Streamlit built-ins over introducing new third-party dependencies or multi-line wrapper functions.
4. **Minimal Code:** Write the absolute minimum lines required to achieve the goal. Do not generate speculative boilerplate, future-proofing code, or decorative scaffolding.

## 2. Output Token Preservation ("Concise Engineer Mode")
- **No Conversational Filler:** Avoid pleasantries, apologies, repeating back the user's prompt, or stating "Certainly! I will now do X".
- **Diff & Result First:** Focus directly on file modifications, command outputs, and concise verification summaries.
- **Telegraphic Status:** Keep status updates to 1–3 short bullet points.

## 3. Graph-First Symbol Discovery (Zero Full-File Dumps)
- **MCP Graph Tools First:** ALWAYS query `codebase-memory-mcp` (`search_graph`, `get_code_snippet`, `trace_call_path`) or inspect `graphify-out/GRAPH_REPORT.md` before reading files.
- **Targeted Line Slices:** If reading a file, use `view_file` with explicit `StartLine` and `EndLine` (e.g., 20–50 lines) rather than dumping full 800+ line files into context.
- **Diff Mode for Edits:** Use `replace_file_content` with small, specific replacement chunks rather than re-writing entire files.

## 4. Quiet Test & Terminal Execution
- **Run Pytest Quietly:** Always execute test suites with `pytest -q --tb=line` (or via `python scripts/project_ops.py test --fast`).
- **Zero Full Log Dumps:** Do not dump passing test outputs into context; report only total passed and specific failing assertion lines.

## 5. Headroom & Session Context Management
- **15-Turn Session Limit:** Encourage starting fresh sessions every 10–15 turns or after completing a discrete sub-task.
- **Obsidian / Working Memory Handoff:** Store session state in `SESSION_LOG.md` / Obsidian rather than carrying multi-turn chat history indefinitely.
