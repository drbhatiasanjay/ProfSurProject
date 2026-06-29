"""Unit tests for models/llm_adapters.py — context builders, classifier,
streaming adapters (mocked), JSON parser, and audit logger."""
import json
import sqlite3
import pytest

from models.llm_adapters import (
    build_company_context,
    build_panel_context,
    classify_query,
    stream_ollama,
    stream_anthropic,
    parse_llm_json,
    log_chat_query,
    count_tokens,
    GROUNDING_FOOTER,
    CONTEXT_BUDGET_TOKENS,
    generate_followup_suggestions,
)


# ---------------------------------------------------------------------------
# Context builder — company-level
# ---------------------------------------------------------------------------

class TestBuildCompanyContext:
    def test_returns_string(self, sample_company_code):
        ctx = build_company_context(sample_company_code, panel_mode="thesis")
        assert isinstance(ctx, str)
        assert len(ctx) > 0

    def test_contains_required_sections(self, sample_company_code):
        ctx = build_company_context(sample_company_code, panel_mode="thesis")
        assert "## [SOURCE: Theory]" in ctx
        assert "## [SOURCE: Thesis (2001-2024)]" in ctx
        assert "Source: Thesis (2001-2024)" in ctx

    def test_token_budget_respected(self, sample_company_code):
        ctx = build_company_context(sample_company_code, panel_mode="thesis")
        assert count_tokens(ctx) <= CONTEXT_BUDGET_TOKENS

    def test_handles_unknown_company_code_gracefully(self):
        ctx = build_company_context(-99999, panel_mode="thesis")
        assert isinstance(ctx, str)
        assert "INSTRUCTIONS" in ctx  # footer always present


# ---------------------------------------------------------------------------
# Context builder — panel-level
# ---------------------------------------------------------------------------

class TestBuildPanelContext:
    def test_returns_string_with_sections(self):
        ctx = build_panel_context(panel_mode="thesis")
        assert isinstance(ctx, str)
        assert "## [SOURCE: Theory]" in ctx
        assert "## [SOURCE: Thesis (2001-2024)]" in ctx
        assert "## [SOURCE: OLS Model]" in ctx
        assert "Source: Thesis (2001-2024)" in ctx

    def test_token_budget_respected(self):
        ctx = build_panel_context(panel_mode="thesis")
        assert count_tokens(ctx) <= CONTEXT_BUDGET_TOKENS


# ---------------------------------------------------------------------------
# Query classifier
# ---------------------------------------------------------------------------

class TestClassifyQuery:
    @pytest.mark.parametrize("q,expected", [
        ("What is the leverage of Reliance?", "factual"),
        ("Show me ROA values for 2020", "factual"),
        ("List all firms in Birth stage", "factual"),
        ("Why is leverage high in this industry?", "analytical"),
        ("Explain the trend", "analytical"),
        ("Recommend a capital strategy", "analytical"),
        ("Compare leverage and show me numbers", "hybrid"),
        ("", "hybrid"),
    ])
    def test_labels(self, q, expected):
        assert classify_query(q) == expected


# ---------------------------------------------------------------------------
# LLM JSON parser
# ---------------------------------------------------------------------------

class TestParseLlmJson:
    def test_valid_json(self):
        raw = '{"answer":"hi","citations":["a"],"followup_questions":["q1"],"chart_request":null}'
        out = parse_llm_json(raw)
        assert out["answer"] == "hi"
        assert out["citations"] == ["a"]
        assert out["followup_questions"] == ["q1"]
        assert out["chart_request"] is None

    def test_json_embedded_in_text(self):
        raw = 'Here is your answer: {"answer":"yes","citations":[]}'
        out = parse_llm_json(raw)
        assert out["answer"] == "yes"
        assert out["citations"] == []

    def test_plain_text_fallback(self):
        raw = "Just a plain reply with no JSON"
        out = parse_llm_json(raw)
        assert out["answer"] == raw
        assert out["citations"] == []
        assert out["followup_questions"] == []
        assert out["chart_request"] is None

    def test_empty_string(self):
        out = parse_llm_json("")
        assert out["answer"] == ""
        assert isinstance(out["citations"], list)

    def test_malformed_json(self):
        out = parse_llm_json('{"answer": "x", broken')
        # Must not raise — falls back to plain-text answer
        assert isinstance(out, dict)
        assert "answer" in out


# ---------------------------------------------------------------------------
# Streaming adapters — monkeypatched (no real API calls)
# ---------------------------------------------------------------------------

class TestStreamOllama:
    def test_yields_strings(self, monkeypatch):
        # Fake ollama.chat returning dict-shaped chunks (matches SDK contract)
        def fake_chat(model, messages, stream, options):
            assert options.get("num_ctx") == 8192, "Must override num_ctx default of 2048"
            assert stream is True
            return iter([
                {"message": {"content": "Hello"}},
                {"message": {"content": " world"}},
                {"message": {"content": ""}},
            ])
        import ollama
        monkeypatch.setattr(ollama, "chat", fake_chat)
        # Re-import to ensure the patched chat is picked up via the function-local import
        from models.llm_adapters import stream_ollama
        chunks = list(stream_ollama([{"role": "user", "content": "hi"}], model="llama3.1:8b"))
        joined = "".join(chunks)
        assert "Hello" in joined
        assert "world" in joined

    def test_handles_missing_sdk(self, monkeypatch):
        import builtins
        real_import = builtins.__import__
        def fake_import(name, *a, **kw):
            if name == "ollama":
                raise ImportError("simulated missing")
            return real_import(name, *a, **kw)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        # Remove cached module so the patched import is triggered
        import sys
        sys.modules.pop("ollama", None)
        from models.llm_adapters import stream_ollama
        chunks = list(stream_ollama([{"role": "user", "content": "hi"}]))
        assert any("not installed" in c.lower() for c in chunks)


class TestStreamAnthropic:
    def test_yields_strings(self, monkeypatch):
        class FakeStreamCtx:
            text_stream = iter(["Hello", " from", " Claude"])
            def __enter__(self): return self
            def __exit__(self, *a): return False
        class FakeMessages:
            def stream(self, **kw):
                assert "model" in kw and "messages" in kw
                return FakeStreamCtx()
        class FakeClient:
            def __init__(self, api_key=None): self.messages = FakeMessages()
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", FakeClient)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        from models.llm_adapters import stream_anthropic
        chunks = list(stream_anthropic([{"role": "user", "content": "hi"}], system="sys"))
        joined = "".join(chunks)
        assert "Hello" in joined
        assert "Claude" in joined

    def test_missing_api_key_yields_message(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # Block streamlit secrets path — use monkeypatch so the module is restored after the test
        monkeypatch.delitem(__import__("sys").modules, "streamlit", raising=False)
        from models.llm_adapters import stream_anthropic
        chunks = list(stream_anthropic([{"role": "user", "content": "hi"}]))
        # Either "not configured" (no key) or "not installed" (no SDK) — both acceptable graceful paths
        joined = " ".join(chunks).lower()
        assert ("not configured" in joined) or ("not installed" in joined)


# ---------------------------------------------------------------------------
# Audit logger
# ---------------------------------------------------------------------------

class TestLogChatQuery:
    def test_writes_audit_row(self, temp_audit_db):
        log_chat_query(
            username="alice",
            role="researcher",
            backend="ollama",
            token_count=237,
            query="What is leverage of Reliance?",
            session_id="sess-123",
        )
        conn = sqlite3.connect(temp_audit_db)
        row = conn.execute(
            "SELECT username, role, page_name, action_type, details, session_id "
            "FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row is not None
        username, role, page_name, action_type, details, session_id = row
        assert username == "alice"
        assert role == "researcher"
        assert page_name == "ai_assistant"
        assert action_type == "ai_query"
        assert session_id == "sess-123"
        d = json.loads(details)
        assert d["llm_backend"] == "ollama"
        assert d["token_count"] == 237
        assert "leverage" in d["query_preview"].lower()

    def test_silent_failure_on_db_error(self, monkeypatch):
        # Force db.get_connection to raise (NOT db._connection — that does not exist)
        import db as db_module
        def boom():
            raise RuntimeError("simulated")
        monkeypatch.setattr(db_module, "get_connection", boom)
        # Must not raise
        log_chat_query("u", "r", "anthropic", 100, "q", "s")


# ---------------------------------------------------------------------------
# generate_followup_suggestions
# ---------------------------------------------------------------------------

class TestGenerateFollowupSuggestions:
    def _fake_client(self, json_text: str):
        class FakeContent:
            text = json_text
        class FakeResponse:
            content = [FakeContent()]
        class FakeMessages:
            def create(self, **kw):
                return FakeResponse()
        class FakeClient:
            def __init__(self, api_key=None):
                self.messages = FakeMessages()
        return FakeClient

    def test_returns_list_on_valid_json(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?", "Q2?", "Q3?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions(
            chat_history=[
                {"role": "user", "content": "How many firms?"},
                {"role": "assistant", "content": "400 firms."},
            ],
            last_query="How many firms?",
            last_response="400 firms.",
            query_type="factual",
        )
        assert result == ["Q1?", "Q2?", "Q3?"]

    def test_returns_empty_on_llm_error(self, monkeypatch):
        class ErrorMessages:
            def create(self, **kw):
                raise RuntimeError("API down")
        class ErrorClient:
            def __init__(self, api_key=None):
                self.messages = ErrorMessages()
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", ErrorClient)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "q", "r", "factual")
        assert result == []

    def test_returns_empty_on_bad_json(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client("Sure, here are some ideas for you to consider."))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "q", "r", "analytical")
        assert result == []

    def test_max_three_items(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "q", "r", "hybrid")
        assert len(result) <= 3

    def test_empty_history_no_crash(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?", "Q2?", "Q3?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions(
            chat_history=[],
            last_query="test",
            last_response="test response",
            query_type="factual",
        )
        assert isinstance(result, list)
