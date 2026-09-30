# PowerShell Test Gate
Write-Host "Running 41-test regression test suite..." -ForegroundColor Cyan
pytest tests/test_p0_remediation.py tests/test_p1_remediation.py tests/test_estimator_suite.py tests/test_citation_inspector.py tests/test_ai_accuracy_benchmark.py tests/test_p2_enhancements.py tests/test_descriptive_analyst.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "PRE-COMMIT TEST GATE FAILED. Aborting commit." -ForegroundColor Red
    exit 1
}
Write-Host "All tests passed successfully!" -ForegroundColor Green
exit 0
