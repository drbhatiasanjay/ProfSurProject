# Start lifecycle-ontology HTTP service on port 8080.
# Requires opam switch 5.2.0 + mingw64-x86_64-openssl installed in opam's Cygwin.
param([int]$Port = 8080)

$opamBin  = "$env:USERPROFILE\.opam\5.2.0\bin"
$cygBin   = "$env:USERPROFILE\.opam\.cygwin\root\bin"
$mingwBin = "$env:USERPROFILE\.opam\.cygwin\root\usr\x86_64-w64-mingw32\sys-root\mingw\bin"
$env:PATH = "$opamBin;$cygBin;$mingwBin;$env:PATH"
$env:OCAMLLIB = "$env:USERPROFILE\.opam\5.2.0\lib\ocaml"

$binary = Join-Path $PSScriptRoot "_build\default\src\cli\main.exe"
if (-not (Test-Path $binary)) {
    Write-Error "Binary not found. Run: cd lifecycle-ontology && dune build"
    exit 1
}

Write-Host "Starting lifecycle-ontology on port $Port ..."
& $binary serve --port $Port
