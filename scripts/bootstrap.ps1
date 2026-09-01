param(
    [switch]$InstallHooks,
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

if ($InstallDependencies) {
    $python = Get-Command py -ErrorAction SilentlyContinue
    if ($python) {
        & py -3.11 -m venv .venv
    } else {
        & python -m venv .venv
    }
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
}

if ($InstallHooks) {
    & git config core.hooksPath .githooks
    Write-Host "Installed Git hooks from .githooks"
}

Write-Host "Bootstrap complete. Use .venv\Scripts\Activate.ps1 before local development."
