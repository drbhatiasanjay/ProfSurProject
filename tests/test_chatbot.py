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


# ---------------------------------------------------------------------------
# count_tokens
# ---------------------------------------------------------------------------

class TestCountTokens:
    def test_normal_string(self):
        n = count_tokens("hello world")
        assert isinstance(n, int) and n > 0

    def test_empty_string_no_crash(self):
        n = count_tokens("")
        assert isinstance(n, int) and n >= 0

    def test_long_text_exceeds_budget(self):
        long = "leverage " * 2000  # ~18 000 chars → 2 000+ tokens (both tiktoken and fallback)
        assert count_tokens(long) > CONTEXT_BUDGET_TOKENS

    def test_returns_int_not_float(self):
        assert isinstance(count_tokens("capital structure"), int)


# ---------------------------------------------------------------------------
# classify_query — real chatbot inputs + edge cases
# ---------------------------------------------------------------------------

class TestClassifyQueryScenarios:
    @pytest.mark.parametrize("q,expected", [
        # "risk" added to analytical_keywords; "which " factual but analytical wins
        ("Which life stage carries the highest default risk in this panel?", "analytical"),
        # "why" analytical beats "which " factual
        ("Which stage carries the highest leverage and why?", "analytical"),
        # "compare" is in hybrid_triggers
        ("Compare GFC leverage vs COVID leverage", "hybrid"),
        # "explain" + "implication" — purely analytical, no factual trigger
        ("Explain the implications of high leverage for firm solvency", "analytical"),
    ])
    def test_real_chatbot_scenarios(self, q, expected):
        assert classify_query(q) == expected

    def test_unicode_no_crash(self):
        result = classify_query("Quel levier est le plus élevé?")
        assert result in ("factual", "analytical", "hybrid")

    def test_very_long_query_no_crash(self):
        result = classify_query("leverage " * 300)
        assert result in ("factual", "analytical", "hybrid")


# ---------------------------------------------------------------------------
# generate_followup_suggestions — negative / edge cases
# ---------------------------------------------------------------------------

class TestGenerateFollowupSuggestionsNegative:
    def _fake_client(self, json_text):
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

    def test_wrong_json_schema_key(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"questions": ["Q1?", "Q2?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        assert generate_followup_suggestions([], "q", "r", "factual") == []

    def test_followups_not_a_list(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": "should be a list"}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        assert generate_followup_suggestions([], "q", "r", "hybrid") == []

    def test_null_items_filtered(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": [null, "Q1?", null]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "q", "r", "factual")
        assert result == ["Q1?"]

    def test_empty_string_items_filtered(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["", "Q1?", ""]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "q", "r", "factual")
        assert result == ["Q1?"]

    def test_empty_list_in_json(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": []}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        assert generate_followup_suggestions([], "q", "r", "factual") == []

    def test_history_missing_content_key(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?", "Q2?", "Q3?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions(
            chat_history=[{"role": "user"}, {"role": "assistant"}],
            last_query="test", last_response="resp", query_type="factual",
        )
        assert isinstance(result, list)

    def test_empty_last_query_no_crash(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?", "Q2?", "Q3?"]}'))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        result = generate_followup_suggestions([], "", "", "factual")
        assert isinstance(result, list)

    def test_truncated_json_returns_empty(self, monkeypatch):
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic",
            self._fake_client('{"followups": ["Q1?'))  # cut off mid-string
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        assert generate_followup_suggestions([], "q", "r", "factual") == []


# ---------------------------------------------------------------------------
# stream_anthropic — role preamble / citations / error paths
# ---------------------------------------------------------------------------

class TestStreamAnthropicScenarios:
    def _make_client(self, captured_kwargs):
        """FakeClient with no .beta attribute → AttributeError → standard fallback captures kwargs."""
        class FakeStreamCtx:
            text_stream = iter(["Mocked response"])
            def __enter__(self): return self
            def __exit__(self, *a): return False
        class FakeMessages:
            def stream(self_, **kw):
                captured_kwargs.update(kw)
                return FakeStreamCtx()
        class FakeClient:
            def __init__(self_, api_key=None):
                self_.messages = FakeMessages()
        return FakeClient

    def test_admin_role_adds_academic_preamble(self, monkeypatch):
        captured = {}
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", self._make_client(captured))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        chunks = list(stream_anthropic([{"role": "user", "content": "hi"}], system="base", role="admin"))
        assert "Mocked response" in "".join(chunks)
        assert "econom" in captured.get("system", "").lower()

    def test_cfo_role_adds_plain_english_preamble(self, monkeypatch):
        captured = {}
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", self._make_client(captured))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        list(stream_anthropic([{"role": "user", "content": "hi"}], system="base", role="cfo"))
        assert "plain" in captured.get("system", "").lower()

    def test_citations_flag_appends_modigliani(self, monkeypatch):
        captured = {}
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", self._make_client(captured))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        list(stream_anthropic([{"role": "user", "content": "hi"}], citations=True))
        assert "Modigliani" in captured.get("system", "")

    def test_stream_api_error_yields_error_string(self, monkeypatch):
        class BrokenMessages:
            def stream(self, **kw): raise RuntimeError("simulated failure")
        class BrokenClient:
            def __init__(self, api_key=None):
                self.messages = BrokenMessages()
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", BrokenClient)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        chunks = list(stream_anthropic([{"role": "user", "content": "hi"}]))
        assert any("error" in c.lower() for c in chunks)

    def test_empty_messages_no_crash(self, monkeypatch):
        captured = {}
        import anthropic
        monkeypatch.setattr(anthropic, "Anthropic", self._make_client(captured))
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
        chunks = list(stream_anthropic([]))
        assert isinstance(chunks, list)


# ---------------------------------------------------------------------------
# stream_ollama — error path
# ---------------------------------------------------------------------------

class TestStreamOllamaNegative:
    def test_model_error_yields_error_message(self, monkeypatch):
        def bad_chat(*a, **kw):
            raise RuntimeError("model not found: llama3.1:8b")
        try:
            import ollama
            monkeypatch.setattr(ollama, "chat", bad_chat)
        except ImportError:
            pytest.skip("ollama not installed")
        from models.llm_adapters import stream_ollama
        chunks = list(stream_ollama([{"role": "user", "content": "hi"}]))
        assert any("error" in c.lower() for c in chunks)


# ---------------------------------------------------------------------------
# generate_econometric_narrative — first tests for this function (0 before)
# ---------------------------------------------------------------------------

class TestGenerateEconometricNarrative:
    @pytest.fixture
    def coef_df(self):
        import pandas as pd
        return pd.DataFrame({
            "Variable": ["profitability", "tangibility", "Intercept"],
            "Coefficient": [-0.32, 0.45, 25.1],
            "Std Error": [0.08, 0.12, 3.2],
            "t-stat": [-4.0, 3.75, 7.8],
            "p-value": [0.001, 0.002, 0.000],
            "Sig": ["***", "***", "***"],
        })

    def _patch(self, monkeypatch, response="Mocked narrative"):
        import models.llm_adapters as _llm
        import db as _db
        monkeypatch.setattr(_llm, "stream_anthropic", lambda *a, **kw: iter([response]))
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)

    def test_no_coef_table_yields_placeholder(self):
        from models.llm_adapters import generate_econometric_narrative
        chunks = list(generate_econometric_narrative(result={}))
        assert "No coefficient" in "".join(chunks)

    def test_normal_call_yields_string(self, monkeypatch, coef_df):
        self._patch(monkeypatch)
        from models.llm_adapters import generate_econometric_narrative
        chunks = list(generate_econometric_narrative(
            {"coef_table": coef_df, "r_squared": 0.42, "n_obs": 5000}
        ))
        assert "".join(chunks) != ""

    def test_cache_hit_skips_llm(self, monkeypatch, coef_df):
        import models.llm_adapters as _llm
        import db as _db
        called = []
        monkeypatch.setattr(_llm, "stream_anthropic", lambda *a, **kw: (called.append(1) or iter(["x"])))
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: "Cached interpretation")
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_econometric_narrative
        chunks = list(generate_econometric_narrative(
            {"coef_table": coef_df, "r_squared": 0.42, "n_obs": 5000}
        ))
        assert "Cached interpretation" in "".join(chunks)
        assert len(called) == 0  # LLM not called on cache hit

    def test_hausman_result_included_in_prompt(self, monkeypatch, coef_df):
        captured_msgs = []
        import models.llm_adapters as _llm
        import db as _db
        def capture(*a, **kw): captured_msgs.extend(a); yield "done"
        monkeypatch.setattr(_llm, "stream_anthropic", capture)
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_econometric_narrative
        list(generate_econometric_narrative(
            {"coef_table": coef_df, "r_squared": 0.42, "n_obs": 5000},
            hausman={"chi2": 5.2, "p_value": 0.02},
        ))
        assert "Hausman" in str(captured_msgs)

    def test_empty_coef_table_no_crash(self, monkeypatch):
        import pandas as pd
        self._patch(monkeypatch)
        from models.llm_adapters import generate_econometric_narrative
        chunks = list(generate_econometric_narrative(
            {"coef_table": pd.DataFrame(), "r_squared": 0, "n_obs": 0}
        ))
        assert isinstance(chunks, list)


# ---------------------------------------------------------------------------
# generate_page_insights — first tests for this function (0 before)
# ---------------------------------------------------------------------------

class TestGeneratePageInsights:
    def _patch(self, monkeypatch, response="Mocked insight"):
        import models.llm_adapters as _llm
        import db as _db
        monkeypatch.setattr(_llm, "stream_anthropic", lambda *a, **kw: iter([response]))
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)

    def _filters(self):
        return {"year_range": (2001, 2024), "panel_mode": "thesis",
                "life_stages": [], "industry_groups": []}

    def test_dashboard_prompt_contains_summarise(self, monkeypatch):
        captured_msgs = []
        import models.llm_adapters as _llm
        import db as _db
        def capture(*a, **kw): captured_msgs.extend(a); yield "done"
        monkeypatch.setattr(_llm, "stream_anthropic", capture)
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_page_insights
        list(generate_page_insights("dashboard", {"mean_leverage": 28.3}, self._filters()))
        assert "Summarise" in str(captured_msgs)

    def test_scenarios_prompt_contains_cfo(self, monkeypatch):
        captured_msgs = []
        import models.llm_adapters as _llm
        import db as _db
        def capture(*a, **kw): captured_msgs.extend(a); yield "done"
        monkeypatch.setattr(_llm, "stream_anthropic", capture)
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_page_insights
        list(generate_page_insights("scenarios", {"predicted": 35.2}, self._filters()))
        assert "CFO" in str(captured_msgs)

    def test_ml_prompt_contains_shap(self, monkeypatch):
        captured_msgs = []
        import models.llm_adapters as _llm
        import db as _db
        def capture(*a, **kw): captured_msgs.extend(a); yield "done"
        monkeypatch.setattr(_llm, "stream_anthropic", capture)
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: None)
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_page_insights
        list(generate_page_insights("ml", {"best_model": "XGBoost"}, self._filters()))
        assert "SHAP" in str(captured_msgs)

    def test_unknown_page_no_crash(self, monkeypatch):
        self._patch(monkeypatch)
        from models.llm_adapters import generate_page_insights
        chunks = list(generate_page_insights("unknown_xyz", {"foo": "bar"}, self._filters()))
        assert isinstance(chunks, list)

    def test_empty_data_summary_no_crash(self, monkeypatch):
        self._patch(monkeypatch)
        from models.llm_adapters import generate_page_insights
        chunks = list(generate_page_insights("dashboard", {}, self._filters()))
        assert isinstance(chunks, list)

    def test_cache_hit_skips_llm(self, monkeypatch):
        import models.llm_adapters as _llm
        import db as _db
        called = []
        monkeypatch.setattr(_llm, "stream_anthropic", lambda *a, **kw: (called.append(1) or iter(["x"])))
        monkeypatch.setattr(_db, "ai_cache_get", lambda *a, **kw: "Cached insight text")
        monkeypatch.setattr(_db, "ai_cache_set", lambda *a, **kw: None)
        from models.llm_adapters import generate_page_insights
        chunks = list(generate_page_insights("dashboard", {"x": 1}, self._filters()))
        assert "Cached insight text" in "".join(chunks)
        assert len(called) == 0

    def test_none_values_in_summary_filtered(self, monkeypatch):
        self._patch(monkeypatch)
        from models.llm_adapters import generate_page_insights
        chunks = list(generate_page_insights("dashboard", {"key": None, "other": 5}, self._filters()))
        assert isinstance(chunks, list)


# ---------------------------------------------------------------------------
# build_company_context — token budget edge case
# ---------------------------------------------------------------------------

class TestBuildCompanyContextEdgeCases:
    def test_token_count_within_budget(self, sample_company_code):
        ctx = build_company_context(sample_company_code, panel_mode="thesis")
        assert count_tokens(ctx) <= CONTEXT_BUDGET_TOKENS


# ---------------------------------------------------------------------------
# build_panel_context — invalid panel_mode edge case
# ---------------------------------------------------------------------------

class TestBuildPanelContextEdgeCases:
    def test_invalid_panel_mode_returns_string(self):
        ctx = build_panel_context(panel_mode="nonexistent_mode_xyz")
        assert isinstance(ctx, str) and len(ctx) > 0


# ---------------------------------------------------------------------------
# log_chat_query — None / boundary inputs
# ---------------------------------------------------------------------------

class TestLogChatQueryEdgeCases:
    def test_none_query_no_crash(self, temp_audit_db):
        log_chat_query("alice", "researcher", "anthropic", 100, None, "s1")

    def test_none_role_no_crash(self, temp_audit_db):
        log_chat_query("alice", None, "anthropic", 100, "q", "s1")

    def test_extreme_token_count_no_crash(self, temp_audit_db):
        log_chat_query("alice", "researcher", "anthropic", 10_000_000, "q", "s1")

    def test_empty_username_stored_as_unknown(self, temp_audit_db):
        log_chat_query("", "researcher", "anthropic", 100, "test query", "s1")
        conn = sqlite3.connect(temp_audit_db)
        row = conn.execute(
            "SELECT username FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "unknown"
