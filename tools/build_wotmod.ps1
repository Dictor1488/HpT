$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\.."
$build = Join-Path $root "build"
$out = Join-Path $build "custom_hpbar_gameface.wotmod"
if (!(Test-Path $build)) { New-Item -ItemType Directory -Path $build | Out-Null }
if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path (Join-Path $root "res") -DestinationPath $out -Force
Write-Host "Built: $out"
