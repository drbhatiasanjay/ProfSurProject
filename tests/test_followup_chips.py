"""
Tests for models.llm_adapters.parse_followup_chips — the parser that splits a
streamed AI Assistant response into (display_text, follow-up chips).

Regression coverage for the AI Assistant bug where a malformed/truncated
FOLLOWUPS_JSON footer leaked onto the screen as raw text (Sonnet answers hit
max_tokens before finishing the footer; the old page-local _parse_chips did
a bare json.loads with no brace scan, fence tolerance, or salvage).

The one invariant every fixture below must satisfy: display_text NEVER
contains the marker, no matter how badly the model deviated from the
instructed footer format.
"""
import pytest

from models.llm_adapters import parse_followup_chips


CLEAN_ANSWER = "Leverage rises with tangibility because collateral supports more debt."

FIXTURES = {
    "clean_valid_footer": (
        f'{CLEAN_ANSWER}\n\n---\n'
        'FOLLOWUPS_JSON: {"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
    ),
    "json_fence": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON:\n```json\n'
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}\n```'
    ),
    "bold_marker": (
        f'{CLEAN_ANSWER}\n\n**FOLLOWUPS_JSON:** '
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
    ),
    "lowercase_spaced_marker": (
        f'{CLEAN_ANSWER}\n\nfollowups_json : '
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
    ),
    "trailing_prose_after_object": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
        '\n\nLet me know if you would like more detail!'
    ),
    "truncated_object_mid_string": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
        '{"followups":["What is the marginal effect of profitability on leverage and how does it compare to size?","How does Pecking Order Theory ex'
    ),
    "truncated_mid_first_string": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
        '{"followups":["What is the marginal effect of profitability on lever'
    ),
    "marker_absent": CLEAN_ANSWER,
    "duplicated_stream": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
        '{"followups":["Duplicate Q1?","Duplicate Q2?","Duplicate Q3?"]}'
    ),
    "empty_followups_list": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: {{"followups":[]}}'
    ),
    "followups_not_a_list": (
        f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: {{"followups":"not a list"}}'
    ),
    "dashes_immediately_before_marker": (
        f'{CLEAN_ANSWER}\n\n---\nFOLLOWUPS_JSON: '
        '{"followups":["What is the mean leverage?","How does Trade-off Theory explain this?","How does this vary by industry?"]}'
    ),
}


class TestParseFollowupChipsInvariant:
    """The regression guard: the raw marker/JSON must never leak into display_text."""

    @pytest.mark.parametrize("name", FIXTURES.keys())
    def test_marker_never_leaks_into_display(self, name):
        display, _chips = parse_followup_chips(FIXTURES[name])
        assert "FOLLOWUPS_JSON" not in display.upper(), (
            f"fixture '{name}' leaked the marker into display_text: {display!r}"
        )

    @pytest.mark.parametrize("name", FIXTURES.keys())
    def test_display_starts_with_clean_answer(self, name):
        display, _chips = parse_followup_chips(FIXTURES[name])
        assert display.startswith(CLEAN_ANSWER)


class TestParseFollowupChipsExtraction:
    def test_clean_valid_footer_extracts_three_chips(self):
        display, chips = parse_followup_chips(FIXTURES["clean_valid_footer"])
        assert display == CLEAN_ANSWER
        assert chips == [
            "What is the mean leverage?",
            "How does Trade-off Theory explain this?",
            "How does this vary by industry?",
        ]

    def test_json_fence_still_extracts_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["json_fence"])
        assert len(chips) == 3

    def test_bold_marker_still_extracts_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["bold_marker"])
        assert len(chips) == 3

    def test_lowercase_spaced_marker_still_extracts_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["lowercase_spaced_marker"])
        assert len(chips) == 3

    def test_trailing_prose_after_object_still_extracts_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["trailing_prose_after_object"])
        assert len(chips) == 3

    def test_truncated_object_salvages_first_complete_question(self):
        _display, chips = parse_followup_chips(FIXTURES["truncated_object_mid_string"])
        assert chips == [
            "What is the marginal effect of profitability on leverage and how does it compare to size?"
        ]

    def test_truncated_mid_first_string_returns_no_chips(self):
        display, chips = parse_followup_chips(FIXTURES["truncated_mid_first_string"])
        assert chips == []
        assert display == CLEAN_ANSWER  # display still clean despite total parse failure

    def test_marker_absent_returns_full_text_and_no_chips(self):
        display, chips = parse_followup_chips(FIXTURES["marker_absent"])
        assert display == CLEAN_ANSWER
        assert chips == []

    def test_duplicated_stream_first_object_wins_no_crash(self):
        _display, chips = parse_followup_chips(FIXTURES["duplicated_stream"])
        assert chips == [
            "What is the mean leverage?",
            "How does Trade-off Theory explain this?",
            "How does this vary by industry?",
        ]

    def test_empty_followups_list_returns_no_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["empty_followups_list"])
        assert chips == []

    def test_followups_not_a_list_returns_no_chips(self):
        _display, chips = parse_followup_chips(FIXTURES["followups_not_a_list"])
        assert chips == []

    def test_dashes_before_marker_not_left_trailing_in_display(self):
        display, chips = parse_followup_chips(FIXTURES["dashes_immediately_before_marker"])
        assert not display.endswith("-")
        assert display == CLEAN_ANSWER
        assert len(chips) == 3


class TestParseFollowupChipsEdgeCases:
    def test_empty_string_input(self):
        display, chips = parse_followup_chips("")
        assert display == ""
        assert chips == []

    def test_chips_capped_at_three(self):
        text = (
            f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
            '{"followups":["Q1?","Q2?","Q3?","Q4?","Q5?"]}'
        )
        _display, chips = parse_followup_chips(text)
        assert len(chips) == 3

    def test_null_and_empty_string_questions_filtered(self):
        text = (
            f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
            '{"followups":[null,"Real question?",""]}'
        )
        _display, chips = parse_followup_chips(text)
        assert chips == ["Real question?"]

    def test_followup_questions_key_also_accepted(self):
        text = (
            f'{CLEAN_ANSWER}\n\nFOLLOWUPS_JSON: '
            '{"followup_questions":["Alt key question?"]}'
        )
        _display, chips = parse_followup_chips(text)
        assert chips == ["Alt key question?"]
