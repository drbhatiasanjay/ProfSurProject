param(
    [string]$Workflow = "Test and Deploy",
    [string]$HealthUrl = "https://lifecycle-leverage-779655496440.us-east1.run.app/_stcore/health"
)

$ErrorActionPreference = "Stop"
$run = gh run list --workflow $Workflow --branch master --limit 1 --json databaseId,status,conclusion,headSha | ConvertFrom-Json
if (-not $run) { throw "No workflow run found." }
Write-Host "Watching run $($run[0].databaseId) at commit $($run[0].headSha)"
gh run watch $run[0].databaseId --exit-status
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing
if ($response.StatusCode -ne 200 -or $response.Content.Trim() -ne "ok") {
    throw "Health check failed: HTTP $($response.StatusCode), body '$($response.Content.Trim())'"
}
Write-Host "Cloud Run health check passed: $HealthUrl"
