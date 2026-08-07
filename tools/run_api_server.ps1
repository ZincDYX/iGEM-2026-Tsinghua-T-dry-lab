param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8080,
  [string]$Python = "py",
  [string]$PythonVersion = "-3.13"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $Root
try {
  & $Python $PythonVersion -c "import sys, numpy, pandas, scipy, sklearn; print('Using Python:', sys.executable); print('numpy/pandas/scipy/sklearn ok')"
  & $Python $PythonVersion -m CatalystOptimizationSystem.api.app $HostName $Port
} finally {
  Pop-Location
}
