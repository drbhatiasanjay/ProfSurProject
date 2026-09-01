param([switch]$PrePush)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

& $python -m py_compile models\agent_tools.py models\llm_adapters.py models\ml_predict.py pages\19_ai_assistant.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($PrePush) {
    $changed = @(git diff --name-only HEAD~1 HEAD)
} else {
    $changed = @(git diff --name-only; git diff --name-only --cached | Sort-Object -Unique)
}
$tests = [System.Collections.Generic.List[string]]::new()
if ($changed -match 'models[\\/]agent_tools|models[\\/]llm_adapters|pages[\\/]19_ai_assistant|tests[\\/]test_gemini|tests[\\/]test_agent_tools|tests[\\/]test_ai_assistant') {
    $tests.Add('tests/test_agent_tools.py')
    $tests.Add('tests/test_gemini_agent.py')
    $tests.Add('tests/test_ai_assistant_e2e.py')
}
if ($changed -match 'models[\\/]ml_predict|tests[\\/]test_models') { $tests.Add('tests/test_models.py') }
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
& $python -m pytest @tests -q --tb=short
exit $LASTEXITCODE
