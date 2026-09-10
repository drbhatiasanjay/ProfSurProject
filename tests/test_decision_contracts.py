"""Contract tests for provider-neutral CFO decision briefs."""

from models.decision_contracts import (
    ActionTraceEvent,
    EvidenceItem,
    GroundingItem,
    ScenarioCase,
    build_decision_brief,
    validate_chart_table,
)


def test_decision_brief_carries_user_visible_trace_without_private_reasoning():
    brief = build_decision_brief(
        answer="Computed result",
        user_query="Summarize leverage",
        intent="descriptive_computation",
        selected_capability="stata.summarize",
        trace=[
            ActionTraceEvent("classify_request", "completed", "descriptive computation"),
            ActionTraceEvent("select_capability", "completed", "stata.summarize"),
            ActionTraceEvent("execute", "completed", "result envelope created"),
        ],
    )

    payload = brief.to_dict()
    assert payload["intent"] == "descriptive_computation"
    assert payload["selected_capability"] == "stata.summarize"
    assert [event["name"] for event in payload["trace"]] == [
        "classify_request",
        "select_capability",
        "execute",
    ]
    assert all("reasoning" not in event for event in payload["trace"])


def test_decision_brief_carries_explicit_grounding_labels():
    brief = build_decision_brief(
        answer="The panel mean is computed from available rows.",
        grounding=[GroundingItem("COMPUTED", "Panel mean", "panel rows")],
    )
    assert brief.to_dict()["grounding"] == (
        {"label": "COMPUTED", "text": "Panel mean", "source": "panel rows"}
    ,)


def test_valid_chart_matches_categories_and_table():
    chart = {
        "chart_type": "line",
        "categories": ["2023", "2024"],
        "series": [{"name": "Leverage", "values": [0.21, 0.24]}],
    }
    result = validate_chart_table(
        [{"year": "2023", "leverage": 0.21}, {"year": "2024", "leverage": 0.24}],
        chart,
    )
    assert result["valid"] is True
    assert result["errors"] == []


def test_mismatched_chart_is_invalid_and_withheld_from_brief():
    chart = {
        "chart_type": "bar",
        "categories": ["Growth", "Maturity", "Decline"],
        "series": [{"name": "Leverage", "values": [0.2, 0.3]}],
    }
    brief = build_decision_brief(answer="Answer", chart=chart, user_query="Compare stages")
    assert brief.chart is None
    assert brief.validation["valid"] is False
    assert any("withheld" in item for item in brief.limitations)


def test_missing_chart_is_valid_for_non_visual_question():
    result = validate_chart_table([], None)
    assert result == {
        "valid": True,
        "chart_present": False,
        "errors": [],
        "warnings": [],
    }


def test_contract_serializes_evidence_and_scenarios():
    brief = build_decision_brief(
        answer="Debt headroom is tighter in the downside case.",
        user_query="What happens if rates rise?",
    )
    brief = brief.__class__(
        **{
            **brief.to_dict(),
            "evidence": (EvidenceItem("Debt", 100, "observed", source="panel"),),
            "scenarios": (ScenarioCase("Downside", {"rate_bps": 200}, {"headroom": 80}),),
        }
    )
    serialized = brief.to_dict()
    assert serialized["evidence"][0]["kind"] == "observed"
    assert serialized["scenarios"][0]["assumptions"]["rate_bps"] == 200

