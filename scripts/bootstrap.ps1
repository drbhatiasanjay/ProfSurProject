param(
    [switch]$InstallHooks,
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

if ($InstallDependencies) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    $venvCreated = $false
    if ($launcher) {
        foreach ($version in @("-3.11", "-3.12", "-3.10")) {
            & py $version --version *> $null
            if ($LASTEXITCODE -eq 0) {
                & py $version -m venv .venv
                if ($LASTEXITCODE -eq 0) { $venvCreated = $true; break }
            }
        }
    }
    if (-not $venvCreated) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            & python -m venv .venv
            $venvCreated = ($LASTEXITCODE -eq 0)
        }
    }
    if (-not $venvCreated) {
        throw "No usable Python runtime found. Install Python 3.11 or 3.12, then rerun this command."
    }
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
}

if ($InstallHooks) {
    & git config core.hooksPath .githooks
    Write-Host "Installed Git hooks from .githooks"
}

Write-Host "Bootstrap complete. Use .venv\Scripts\Activate.ps1 before local development."
