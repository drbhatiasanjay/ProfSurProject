"""
Tests for persistent chat session functions in db.py.
Uses temp_chat_db fixture (temp SQLite, monkeypatched db.get_connection).
"""
import sqlite3
import pytest
import db


# ── TestChatSessions ─────────────────────────────────────────────────────────

class TestChatSessions:
    def test_create_session_row_exists(self, temp_chat_db):
        db.create_chat_session("cs_001", "sbhatia", "admin")
        conn = sqlite3.connect(temp_chat_db)
        row = conn.execute(
            "SELECT username, role, mode, panel_mode FROM chat_sessions WHERE chat_session_id='cs_001'"
        ).fetchone()
        conn.close()
        assert row == ("sbhatia", "admin", "Researcher", "thesis")

    def test_create_session_default_title_is_null(self, temp_chat_db):
        db.create_chat_session("cs_002", "sbhatia", "admin")
        conn = sqlite3.connect(temp_chat_db)
        title = conn.execute(
            "SELECT title FROM chat_sessions WHERE chat_session_id='cs_002'"
        ).fetchone()[0]
        conn.close()
        assert title is None

    def test_create_session_with_company_code(self, temp_chat_db):
        db.create_chat_session("cs_003", "skumar", "researcher", company_code=22859)
        conn = sqlite3.connect(temp_chat_db)
        code = conn.execute(
            "SELECT company_code FROM chat_sessions WHERE chat_session_id='cs_003'"
        ).fetchone()[0]
        conn.close()
        assert code == 22859

    def test_list_sessions_ordered_by_last_active_desc(self, temp_chat_db):
        db.create_chat_session("cs_a", "user1", "viewer")
        db.create_chat_session("cs_b", "user1", "viewer")
        # Push cs_a into the past so ordering is deterministic
        conn = sqlite3.connect(temp_chat_db)
        conn.execute("UPDATE chat_sessions SET last_active='2020-01-01 00:00:00' WHERE chat_session_id='cs_a'")
        conn.commit()
        conn.close()
        db.append_chat_message("cs_b", "user", "hello")
        sessions = db.list_chat_sessions("user1")
        assert sessions[0]["chat_session_id"] == "cs_b"

    def test_list_sessions_username_isolation(self, temp_chat_db):
        db.create_chat_session("cs_u1", "alice", "admin")
        db.create_chat_session("cs_u2", "bob", "researcher")
        alice_sessions = db.list_chat_sessions("alice")
        bob_sessions = db.list_chat_sessions("bob")
        assert all(s["chat_session_id"] == "cs_u1" for s in alice_sessions)
        assert all(s["chat_session_id"] == "cs_u2" for s in bob_sessions)

    def test_list_sessions_limit_respected(self, temp_chat_db):
        for i in range(5):
            db.create_chat_session(f"cs_lim_{i}", "limuser", "viewer")
        sessions = db.list_chat_sessions("limuser", limit=3)
        assert len(sessions) == 3

    def test_list_sessions_empty_for_unknown_user(self, temp_chat_db):
        assert db.list_chat_sessions("nobody") == []

    def test_delete_session_removes_row(self, temp_chat_db):
        db.create_chat_session("cs_del", "sbhatia", "admin")
        db.delete_chat_session("cs_del")
        conn = sqlite3.connect(temp_chat_db)
        row = conn.execute(
            "SELECT 1 FROM chat_sessions WHERE chat_session_id='cs_del'"
        ).fetchone()
        conn.close()
        assert row is None

    def test_delete_session_cascades_to_messages(self, temp_chat_db):
        db.create_chat_session("cs_casc", "sbhatia", "admin")
        db.append_chat_message("cs_casc", "user", "hello")
        db.append_chat_message("cs_casc", "assistant", "world")
        db.delete_chat_session("cs_casc")
        conn = sqlite3.connect(temp_chat_db)
        count = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE chat_session_id='cs_casc'"
        ).fetchone()[0]
        conn.close()
        assert count == 0


# ── TestChatMessages ─────────────────────────────────────────────────────────

class TestChatMessages:
    def setup_method(self):
        pass

    def test_append_user_message(self, temp_chat_db):
        db.create_chat_session("cs_msg1", "sbhatia", "admin")
        db.append_chat_message("cs_msg1", "user", "What is leverage?")
        msgs = db.load_chat_messages("cs_msg1")
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "What is leverage?"

    def test_append_assistant_message_with_metadata(self, temp_chat_db):
        db.create_chat_session("cs_msg2", "sbhatia", "admin")
        db.append_chat_message("cs_msg2", "assistant", "Leverage is debt/equity.",
                               model_used="claude-haiku-4-5-20251001", elapsed_s=1.23)
        msgs = db.load_chat_messages("cs_msg2")
        assert msgs[0]["model_used"] == "claude-haiku-4-5-20251001"
        assert msgs[0]["elapsed_s"] == pytest.approx(1.23)

    def test_load_messages_in_ts_asc_order(self, temp_chat_db):
        db.create_chat_session("cs_order", "sbhatia", "admin")
        db.append_chat_message("cs_order", "user", "Q1")
        db.append_chat_message("cs_order", "assistant", "A1")
        db.append_chat_message("cs_order", "user", "Q2")
        msgs = db.load_chat_messages("cs_order")
        assert [m["content"] for m in msgs] == ["Q1", "A1", "Q2"]

    def test_load_unknown_session_returns_empty(self, temp_chat_db):
        assert db.load_chat_messages("cs_nonexistent") == []

    def test_auto_title_set_from_first_user_message(self, temp_chat_db):
        db.create_chat_session("cs_title", "sbhatia", "admin")
        db.append_chat_message("cs_title", "user", "What is the mean leverage for Maturity stage firms?")
        conn = sqlite3.connect(temp_chat_db)
        title = conn.execute(
            "SELECT title FROM chat_sessions WHERE chat_session_id='cs_title'"
        ).fetchone()[0]
        conn.close()
        assert title == "What is the mean leverage for Maturity stage firms?"

    def test_auto_title_truncated_to_60_chars(self, temp_chat_db):
        long_q = "A" * 100
        db.create_chat_session("cs_trunc", "sbhatia", "admin")
        db.append_chat_message("cs_trunc", "user", long_q)
        conn = sqlite3.connect(temp_chat_db)
        title = conn.execute(
            "SELECT title FROM chat_sessions WHERE chat_session_id='cs_trunc'"
        ).fetchone()[0]
        conn.close()
        assert len(title) == 60

    def test_auto_title_not_overwritten_by_assistant_message(self, temp_chat_db):
        db.create_chat_session("cs_notitle", "sbhatia", "admin")
        db.append_chat_message("cs_notitle", "user", "First question")
        db.append_chat_message("cs_notitle", "assistant", "An answer that should NOT become the title")
        conn = sqlite3.connect(temp_chat_db)
        title = conn.execute(
            "SELECT title FROM chat_sessions WHERE chat_session_id='cs_notitle'"
        ).fetchone()[0]
        conn.close()
        assert title == "First question"

    def test_chat_title_can_be_updated_and_is_bounded(self, temp_chat_db):
        db.create_chat_session("cs_rename", "sbhatia", "admin")
        db.update_chat_session_title("cs_rename", "  A   renamed   research   session  ")
        sessions = db.list_chat_sessions("sbhatia")
        session = next(item for item in sessions if item["chat_session_id"] == "cs_rename")
        assert session["title"] == "A renamed research session"

    def test_assistant_feedback_is_persisted(self, temp_chat_db):
        db.create_chat_session("cs_feedback", "sbhatia", "admin")
        db.append_chat_message("cs_feedback", "assistant", "Answer")
        message_id = db.load_chat_messages("cs_feedback")[0]["id"]
        db.set_chat_message_feedback(message_id, "useful")
        assert db.load_chat_messages("cs_feedback")[0]["feedback"] == "useful"

    def test_message_count_increments(self, temp_chat_db):
        db.create_chat_session("cs_count", "sbhatia", "admin")
        for i in range(4):
            db.append_chat_message("cs_count", "user", f"msg {i}")
        conn = sqlite3.connect(temp_chat_db)
        count = conn.execute(
            "SELECT message_count FROM chat_sessions WHERE chat_session_id='cs_count'"
        ).fetchone()[0]
        conn.close()
        assert count == 4

    def test_session_list_shows_message_count(self, temp_chat_db):
        db.create_chat_session("cs_cnt2", "sbhatia", "admin")
        db.append_chat_message("cs_cnt2", "user", "hello")
        db.append_chat_message("cs_cnt2", "assistant", "hi")
        sessions = db.list_chat_sessions("sbhatia")
        assert sessions[0]["message_count"] == 2


# ── TestChatPersistenceEdgeCases ─────────────────────────────────────────────

class TestChatPersistenceEdgeCases:
    def test_create_session_duplicate_id_is_noop(self, temp_chat_db):
        db.create_chat_session("cs_dup", "sbhatia", "admin")
        db.create_chat_session("cs_dup", "other_user", "viewer")
        # original row should survive
        conn = sqlite3.connect(temp_chat_db)
        row = conn.execute(
            "SELECT username FROM chat_sessions WHERE chat_session_id='cs_dup'"
        ).fetchone()
        conn.close()
        assert row[0] == "sbhatia"

    def test_delete_nonexistent_session_no_crash(self, temp_chat_db):
        db.delete_chat_session("cs_does_not_exist")

    def test_append_to_nonexistent_session_no_crash(self, temp_chat_db):
        # FK violation is silently swallowed
        db.append_chat_message("cs_ghost", "user", "hello")

    def test_load_messages_empty_session_no_crash(self, temp_chat_db):
        db.create_chat_session("cs_empty", "sbhatia", "admin")
        assert db.load_chat_messages("cs_empty") == []

    def test_list_sessions_returns_dict_keys(self, temp_chat_db):
        db.create_chat_session("cs_keys", "sbhatia", "admin")
        sessions = db.list_chat_sessions("sbhatia")
        assert len(sessions) == 1
        expected_keys = {"chat_session_id", "title", "started_at", "last_active", "message_count", "mode"}
        assert expected_keys <= set(sessions[0].keys())

    def test_silent_failure_when_db_table_missing(self, tmp_path, monkeypatch):
        # Redirect to a DB with NO chat tables — all calls should be silent no-ops
        p = tmp_path / "empty.db"
        sqlite3.connect(str(p)).close()

        def _bad_conn():
            return sqlite3.connect(str(p))

        import db as db_mod
        monkeypatch.setattr(db_mod, "get_connection", _bad_conn)

        db.create_chat_session("cs_x", "u", "viewer")
        db.append_chat_message("cs_x", "user", "q")
        assert db.load_chat_messages("cs_x") == []
        assert db.list_chat_sessions("u") == []
        db.delete_chat_session("cs_x")


# ── TestChatSessionLifecycle ──────────────────────────────────────────────────

class TestChatSessionLifecycle:
    def test_multi_turn_conversation_round_trip(self, temp_chat_db):
        db.create_chat_session("cs_conv", "sbhatia", "admin", panel_mode="latest", mode="CFO")
        db.append_chat_message("cs_conv", "user", "What is leverage?")
        db.append_chat_message("cs_conv", "assistant", "Leverage is LTD/equity.",
                               model_used="claude-haiku-4-5-20251001", elapsed_s=0.5)
        db.append_chat_message("cs_conv", "user", "What does pecking order say?")
        db.append_chat_message("cs_conv", "assistant", "POT says internal funds first.",
                               model_used="claude-sonnet-4-6", elapsed_s=1.1)

        msgs = db.load_chat_messages("cs_conv")
        assert len(msgs) == 4
        assert msgs[0]["role"] == "user"
        assert msgs[1]["model_used"] == "claude-haiku-4-5-20251001"
        assert msgs[3]["elapsed_s"] == pytest.approx(1.1)

    def test_switching_sessions_loads_correct_messages(self, temp_chat_db):
        db.create_chat_session("cs_s1", "sbhatia", "admin")
        db.create_chat_session("cs_s2", "sbhatia", "admin")
        db.append_chat_message("cs_s1", "user", "Session 1 question")
        db.append_chat_message("cs_s2", "user", "Session 2 question")

        msgs_s1 = db.load_chat_messages("cs_s1")
        msgs_s2 = db.load_chat_messages("cs_s2")
        assert msgs_s1[0]["content"] == "Session 1 question"
        assert msgs_s2[0]["content"] == "Session 2 question"

    def test_new_session_after_delete_active(self, temp_chat_db):
        db.create_chat_session("cs_old", "sbhatia", "admin")
        db.append_chat_message("cs_old", "user", "old question")
        db.delete_chat_session("cs_old")

        db.create_chat_session("cs_new", "sbhatia", "admin")
        db.append_chat_message("cs_new", "user", "new question")
        sessions = db.list_chat_sessions("sbhatia")
        assert len(sessions) == 1
        assert sessions[0]["chat_session_id"] == "cs_new"


# ── TestFollowupPersistence ───────────────────────────────────────────────────
# Follow-up chips must survive page reload and chat-session switching —
# see pages/19_ai_assistant.py "Continue exploring" hydration on load.

class TestFollowupPersistence:
    def test_followups_round_trip(self, temp_chat_db):
        db.create_chat_session("cs_fup1", "sbhatia", "admin")
        chips = ["What is the mean leverage?", "Why does POT predict this?", "How does it vary by industry?"]
        db.append_chat_message("cs_fup1", "assistant", "Leverage is 0.42.",
                               model_used="claude-haiku-4-5-20251001", elapsed_s=1.0,
                               followups=chips)
        msgs = db.load_chat_messages("cs_fup1")
        assert msgs[0]["followups"] == chips

    def test_chart_spec_round_trip(self, temp_chat_db):
        db.create_chat_session("cs_chart", "sbhatia", "admin")
        spec = {"chart_type": "line", "categories": ["2020", "2021"],
                "series": [{"name": "ROA", "values": [0.1, 0.2]}]}
        db.append_chat_message("cs_chart", "assistant", "Chart answer", chart_spec=spec)
        msgs = db.load_chat_messages("cs_chart")
        assert msgs[0]["chart_spec"] == spec

    def test_list_sessions_includes_company_code(self, temp_chat_db):
        db.create_chat_session("cs_company", "sbhatia", "admin", mode="CFO", company_code=22859)
        sessions = db.list_chat_sessions("sbhatia")
        assert sessions[0]["company_code"] == 22859

    def test_user_message_has_no_followups(self, temp_chat_db):
        db.create_chat_session("cs_fup2", "sbhatia", "admin")
        db.append_chat_message("cs_fup2", "user", "What is leverage?")
        msgs = db.load_chat_messages("cs_fup2")
        assert msgs[0]["followups"] == []

    def test_legacy_row_with_null_followups_returns_empty_list(self, temp_chat_db):
        # Simulates a row written before migration 005 — followups column NULL
        db.create_chat_session("cs_fup3", "sbhatia", "admin")
        db.append_chat_message("cs_fup3", "assistant", "Answer without chips.")
        msgs = db.load_chat_messages("cs_fup3")
        assert msgs[0]["followups"] == []

    def test_malformed_followups_json_returns_empty_list(self, temp_chat_db):
        db.create_chat_session("cs_fup4", "sbhatia", "admin")
        db.append_chat_message("cs_fup4", "assistant", "Answer.")
        conn = sqlite3.connect(temp_chat_db)
        conn.execute(
            "UPDATE chat_messages SET followups = ? WHERE chat_session_id = 'cs_fup4'",
            ("not valid json {",),
        )
        conn.commit()
        conn.close()
        msgs = db.load_chat_messages("cs_fup4")
        assert msgs[0]["followups"] == []

    def test_empty_followups_list_stored_as_null(self, temp_chat_db):
        db.create_chat_session("cs_fup5", "sbhatia", "admin")
        db.append_chat_message("cs_fup5", "assistant", "Answer.", followups=[])
        conn = sqlite3.connect(temp_chat_db)
        raw = conn.execute(
            "SELECT followups FROM chat_messages WHERE chat_session_id='cs_fup5'"
        ).fetchone()[0]
        conn.close()
        assert raw is None


# ── TestChatSessionUpdates ──────────────────────────────────────────────────

class TestChatSessionUpdates:
    def test_update_session_mode(self, temp_chat_db):
        db.create_chat_session("cs_up1", "sbhatia", "admin", mode="Researcher")
        db.update_chat_session_mode("cs_up1", "CFO")
        sessions = db.list_chat_sessions("sbhatia")
        assert any(s["chat_session_id"] == "cs_up1" and s["mode"] == "CFO" for s in sessions)

    def test_update_session_company(self, temp_chat_db):
        db.create_chat_session("cs_up2", "sbhatia", "admin", mode="CFO", company_code=22859)
        db.update_chat_session_company("cs_up2", 12345)
        conn = sqlite3.connect(temp_chat_db)
        code = conn.execute(
            "SELECT company_code FROM chat_sessions WHERE chat_session_id='cs_up2'"
        ).fetchone()[0]
        conn.close()
        assert code == 12345
