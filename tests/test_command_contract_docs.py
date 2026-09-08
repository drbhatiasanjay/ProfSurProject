"""Ensure documented canonical Stata syntax remains parseable."""

import re
from pathlib import Path

from models.stata_engine import parse_stata_command


ROOT = Path(__file__).resolve().parents[1]


def test_documented_stata_examples_have_valid_parser_contracts():
    text = (ROOT / "docs" / "WAVE5_COMMAND_CONTRACTS.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```stata\n(.*?)```", text, flags=re.DOTALL)
    commands = [line.strip() for block in blocks for line in block.splitlines() if line.strip()]
    assert commands
    for command in commands:
        parsed = parse_stata_command(command)
        assert parsed["cmd"]
        assert not parsed.get("parse_error"), f"{command}: {parsed.get('parse_error')}"


def test_documented_structured_option_examples_match_parser_output():
    scenario = parse_stata_command("scenario leverage tax=-0.05")
    scenario_alt = parse_stata_command(
        "scenario leverage, interventions(tax=-0.05)"
    )
    hdfe = parse_stata_command(
        "hdfe leverage profitability, absorb(company_code year)"
    )
    assert scenario["options"]["interventions"] == {"tax": -0.05}
    assert scenario_alt["options"]["interventions"] == {"tax": -0.05}
    assert hdfe["options"]["absorb"] == ["company_code", "year"]
