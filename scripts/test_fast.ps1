param([switch]$PrePush)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

if ($PrePush) {
    $changed = @(git diff --name-only HEAD~1 HEAD 2>$null)
} else {
    $changed = @(git diff --name-only 2>$null; git diff --name-only --cached 2>$null | Sort-Object -Unique)
}

# Smart Hook: If only documentation, markdown, or non-executable artifacts changed, skip tests
$codeFiles = @($changed | Where-Object { 
    $_ -match '\.(py|toml|yaml|yml|json|sql|sh|ps1)$' -and $_ -notmatch '^(docs|paper)[\\/]' 
})

if ($changed.Count -gt 0 -and $codeFiles.Count -eq 0) {
    Write-Host "Smart Hook: Only documentation, markdown, or media changed. Fast checks passed."
    exit 0
}

$python = "python"
$venvPy = Join-Path $repo ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    try {
        & $venvPy -m pytest --version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $python = $venvPy }
    } catch {}
}

& $python -m py_compile models\agent_tools.py models\llm_adapters.py models\ml_predict.py models\stata_engine.py pages\19_ai_assistant.py pages\23_stata_studio.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$tests = [System.Collections.Generic.List[string]]::new()
if ($changed -match 'models[\\/]agent_tools|models[\\/]llm_adapters|models[\\/]stata_engine|pages[\\/]19_ai_assistant|pages[\\/]23_stata_studio|tests[\\/]test_gemini|tests[\\/]test_agent_tools|tests[\\/]test_ai_assistant|tests[\\/]test_stata_engine') {
    $tests.Add('tests/test_agent_tools.py')
    $tests.Add('tests/test_gemini_agent.py')
    $tests.Add('tests/test_ai_assistant_e2e.py')
    $tests.Add('tests/test_stata_engine.py')
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
