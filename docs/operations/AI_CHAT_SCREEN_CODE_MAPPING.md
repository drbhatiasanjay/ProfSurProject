# AI Chat Screen ↔ Code Mapping

## Canonical launch

The only supported local launch is the repository-root `app.py` on port 8501:

```powershell
py -3.12 -m streamlit run app.py --server.port 8501 --server.headless true
```

Launching `pages/19_ai_assistant.py` directly is archived/deprecated. It bypasses
the current shell and produces Streamlit's legacy lowercase auto-discovered page
list—the exact symptom previously seen in the demo.

## Mapping

| Screen area | Canonical source | Contract |
|---|---|---|
| Fixed header / dataset / signed-in identity | `app.py` (`lc-navbar`, global sidebar) | Must appear on every authenticated page |
| Main navigation | `app.py` (`st.Page`, `st.navigation`) | One registered route per visible page |
| AI page shell and session bootstrap | `pages/19_ai_assistant.py` | Loads the active chat session and history |
| AI mode/backend/API controls | `pages/19_ai_assistant.py` page sidebar | Extends the global sidebar; never replaces navigation |
| Chat input and submit | `pages/19_ai_assistant.py` chat input path | Adds user/assistant turns and reruns safely |
| Stata command execution from AI | `models/stata_engine.py` via `execute_stata_command` | Renders terminal output, interpretation, and charts |
| Chat persistence | `db.py` `append_chat_message` / `load_chat_messages` | Follow-up chips and chart specs survive reload |
| Stata Studio | `pages/23_stata_studio.py` registered by `app.py` | Must be reached through the canonical sidebar |

## Demo acceptance checks

1. Open the root URL and sign in.
2. Confirm the fixed `LifeCycle Leverage` header and title-case sidebar are visible.
3. Click `AI Assistant` in the sidebar; do not type `/ai_assistant` into a stale
   legacy tab.
4. Submit one natural-language question and one Stata command.
5. Confirm the response, follow-up actions, chart/metadata where applicable, and
   the same current sidebar remain visible after rerun.
6. Repeat the authenticated path for all four configured profiles.

## Archived legacy behavior

The legacy direct-page launch is retained only as historical context; it is not a
supported demo or regression target. Any screenshot showing lowercase auto-
discovered navigation or missing `lc-navbar` is an entrypoint/process failure and
must be rejected as invalid evidence.
