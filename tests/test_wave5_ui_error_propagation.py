"""Cross-layer error propagation contracts for both Wave 5 UI consumers."""

import uuid
from pathlib import Path

import pandas as pd

from models.analytical_contracts import AnalyticalRequest, fingerprint_df
from models.analytical_router import route
from models.stata_engine import ModelResultContext, parse_stata_command


def _ui_request(command: str) -> AnalyticalRequest:
    frame = pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [0.1, 0.2, 0.3]})
    return AnalyticalRequest(
        command_str=command,
        parsed=parse_stata_command(command),
        df=frame,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=fingerprint_df(frame),
        session_id="ui-session",
        session_context=ModelResultContext(),
    )


def test_ai_assistant_boundary_receives_typed_validation_error_without_success_payload():
    result = route(_ui_request("graph box y, over(missing_group)"))
    payload = result.to_dict()

    assert payload["status"] == "error"
    assert payload["error_code"] == "VARIABLE_NOT_FOUND"
    assert payload["metadata"]["stata_rc"] == 111
    assert payload["message"]
    assert payload.get("coefficients") is None


def test_stata_studio_boundary_receives_no_active_estimation_error():
    result = route(_ui_request("test x = 0"))
    payload = result.to_dict()

    assert payload["status"] == "error"
    assert payload["error_code"] == "NO_ACTIVE_ESTIMATION"
    assert payload["message"]
    assert payload.get("coefficients") is None


def test_stata_command_input_has_stable_session_key_for_follow_on_submissions():
    source = (Path(__file__).parents[1] / "pages" / "23_stata_studio.py").read_text(encoding="utf-8")
    input_block = source[source.index('typed_cmd = st.text_input('):source.index('trigger_run =', source.index('typed_cmd = st.text_input('))]
    assert 'key="stata_cmd_input"' in input_block
    assert 'value=st.session_state.get("stata_cmd_input", "")' not in input_block
