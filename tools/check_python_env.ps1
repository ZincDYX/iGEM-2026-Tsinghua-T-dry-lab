param(
  [string]$Python = "py",
  [string]$PythonVersion = "-3.13"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $Root
try {
  & $Python $PythonVersion -c @"
import sys
print('python_executable:', sys.executable)
print('python_version:', sys.version)

import numpy
import pandas
import scipy
import sklearn

print('numpy:', numpy.__version__)
print('pandas:', pandas.__version__)
print('scipy:', scipy.__version__)
print('sklearn:', sklearn.__version__)
print('environment: ok')
"@
} finally {
  Pop-Location
}
