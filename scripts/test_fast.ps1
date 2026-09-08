param([switch]$PrePush)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
if (-not $env:PROFSUR_DB_PATH) {
    $env:PROFSUR_DB_PATH = Join-Path $env:TEMP "profsur-fast-$PID.db"
    Copy-Item -LiteralPath (Join-Path $repo "capital_structure.db") -Destination $env:PROFSUR_DB_PATH -Force
}

    & $python -m py_compile models\agent_tools.py models\llm_adapters.py models\ml_predict.py models\stata_engine.py models\stata_syntax.py models\stata_validation.py models\capability_status.py pages\19_ai_assistant.py pages\23_stata_studio.py scripts\check_import_side_effects.py scripts\check_stata_contracts.py scripts\render_capability_status.py scripts\wave5_realdata_audit.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python scripts\check_stata_contracts.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python scripts\check_import_side_effects.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python scripts\render_capability_status.py --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($PrePush) {
    $changed = @(git diff --name-only HEAD~1 HEAD)
} else {
    $changed = @(git diff --name-only; git diff --name-only --cached | Sort-Object -Unique)
}
$tests = [System.Collections.Generic.List[string]]::new()
if ($changed -match 'models[\\/]agent_tools|models[\\/]llm_adapters|models[\\/]stata_engine|pages[\\/]19_ai_assistant|pages[\\/]23_stata_studio|tests[\\/]test_gemini|tests[\\/]test_agent_tools|tests[\\/]test_ai_assistant|tests[\\/]test_stata_engine') {
    $tests.Add('tests/test_agent_tools.py')
    $tests.Add('tests/test_gemini_agent.py')
    $tests.Add('tests/test_ai_assistant_e2e.py')
    $tests.Add('tests/test_stata_engine.py')
}
if ($changed -match 'models[\\/]ml_predict|tests[\\/]test_models') { $tests.Add('tests/test_models.py') }
if ($changed -match 'models[\\/](stata_engine|stata_validation|analytical_router|capability_status|command_registry|econometric|causal_adapters|gmm_adapter|ml_adapters|scenario_capability)|pages[\\/](13_advanced_econometrics|23_stata_studio)|docs[\\/](WAVE5_COMMAND_CONTRACTS|CAPABILITY_STATUS)|tests[\\/]test_wave5') {
    $tests.Add('tests/test_wave5_independent_review_repair.py')
    $tests.Add('tests/test_capability_status_contract.py')
    $tests.Add('tests/test_command_contract_docs.py')
}
if ($changed -match 'models[\\/]llm_adapters|Dockerfile|tests[\\/]test_llm_adapter_import_safety') {
    $tests.Add('tests/test_llm_adapter_import_safety.py')
    $tests.Add('tests/test_chatbot.py')
}
if ($changed -match 'db[.]py|tests[\\/]test_chat|tests[\\/]test_user_state') {
    $tests.Add('tests/test_chat_persistence.py')
    $tests.Add('tests/test_user_state.py')
}
$tests = @($tests | Sort-Object -Unique)
if ($tests.Count -eq 0) {
    Write-Host "Fast checks passed; no targeted Python tests selected."
    exit 0
}
Write-Host ("Running targeted tests: " + ($tests -join ", "))
        & $python -m pytest @tests -q --tb=short --basetemp (Join-Path $env:TEMP "profsur-pytest-$PID")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if ($PrePush -and $changed -match 'models[\\/](stata_engine|stata_validation|analytical_router|econometric|causal_adapters|gmm_adapter|ml_adapters|scenario_capability)') {
    Write-Host "Running disposable 9,031-row real-data audit."
    & $python scripts\wave5_realdata_audit.py --source-db (Join-Path $repo "capital_structure.db") --quiet
}
exit $LASTEXITCODE
