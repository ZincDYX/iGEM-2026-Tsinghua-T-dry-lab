# Windows source-to-desktop entry. Scientific tools are not installed or run.
[CmdletBinding()]
param(
    [string]$Python = '',
    [string]$Output = '',
    [string]$DownloadCache = '',
    [switch]$Check
)
$ErrorActionPreference = 'Stop'
$repo = $PSScriptRoot
$config = Get-Content -LiteralPath (Join-Path $repo 'requirements/release-toolchain.json') -Raw | ConvertFrom-Json

function Run-Checked([string]$Program, [string[]]$Arguments) {
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed. See the error above; no package has been declared ready." }
}
function Require-Program([string]$Name) {
    $command = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command) { throw "Missing $Name. See README.md > Build your own Windows desktop." }
    return $command.Source
}

if ($env:OS -ne 'Windows_NT') { throw 'This desktop entry supports Windows x64 only.' }
if (-not $Python) {
    $existing = Join-Path $repo '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $existing) { $Python = $existing }
    elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $Python = & py.exe -3.13 -B -c 'import sys; print(sys.executable)'
        if ($LASTEXITCODE -ne 0) { throw "Install Python $($config.python) x64, or pass -Python its full path." }
    }
    else { $Python = Require-Program 'python.exe' }
}
$details = & $Python -B -c "import json,struct,sys; print(json.dumps(dict(version='.'.join(map(str,sys.version_info[:3])),bits=struct.calcsize('P')*8,implementation=sys.implementation.name)))"
if ($LASTEXITCODE -ne 0) { throw 'Cannot start the selected Python. Pass -Python its full path.' }
$details = $details | ConvertFrom-Json
if ($details.version -ne $config.python -or $details.bits -ne 64 -or $details.implementation -ne 'cpython') {
    throw "Requires CPython $($config.python) x64; selected $($details.version) / $($details.bits)-bit. Pass -Python the correct executable."
}
$node = Require-Program 'node.exe'
$git = Require-Program 'git.exe'
$rustup = Require-Program 'rustup.exe'
$nodeVersion = & $node --version
if ($LASTEXITCODE -ne 0 -or $nodeVersion -ne "v$($config.node)") { throw "Install Node $($config.node) x64 and reopen the terminal." }
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio/Installer/vswhere.exe'
if (-not (Get-Command cl.exe -ErrorAction SilentlyContinue)) {
    if (-not (Test-Path -LiteralPath $vswhere)) { throw 'Install Visual Studio Build Tools: Desktop development with C++ and Windows SDK. See README.md.' }
    $vc = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($LASTEXITCODE -ne 0 -or -not $vc) { throw 'Install the Desktop development with C++ workload and Windows SDK in Visual Studio Build Tools.' }
}
if ($Check) {
    Write-Host 'Prerequisites found. Build will prepare the pinned Rust/pnpm versions and Python environment.'
    Write-Host 'No dependencies were installed and no build or scientific calculation was run.'
    exit 0
}
$dirty = & $git -C $repo status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'Use git clone to obtain the source, not the source ZIP. See README.md.' }
if ($dirty) { throw 'Build from a clean Git checkout. Keep your changes; commit them before building.' }
if (-not $Output) { $Output = Join-Path $repo 'build/releases/FusionLab' }
if (-not $DownloadCache) { $DownloadCache = Join-Path $repo 'build/release-cache' }
$Output = [IO.Path]::GetFullPath($Output)
$DownloadCache = [IO.Path]::GetFullPath($DownloadCache)
if ((Test-Path -LiteralPath $Output) -or (Test-Path -LiteralPath ($Output+'.zip'))) {
    throw 'Output already exists. Keep the old release and use -Output with a new folder.'
}

$previousPath = $env:Path
$previousRust = $env:RUSTUP_TOOLCHAIN
$previousBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    # Process-scoped override: do not change the user's global Rust default.
    $env:RUSTUP_TOOLCHAIN = "$($config.rust)-x86_64-pc-windows-msvc"
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $installed = & $rustup toolchain list
    if ($LASTEXITCODE -ne 0) { throw 'Cannot list Rust toolchains.' }
    if (-not ($installed | Where-Object { $_.Split(' ')[0] -eq $env:RUSTUP_TOOLCHAIN })) {
        Run-Checked -Program $rustup -Arguments @('toolchain','install',$env:RUSTUP_TOOLCHAIN,'--profile','minimal')
    }
    $pnpm = Get-Command pnpm.cmd -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $ready = $false
    if ($pnpm) { $version = & $pnpm.Source --version; $ready = $LASTEXITCODE -eq 0 -and $version -eq $config.pnpm }
    if (-not $ready) {
        $npm = Require-Program 'npm.cmd'
        $tools = Join-Path $repo 'build/desktop-tools'
        Run-Checked -Program $npm -Arguments @('install','--prefix',$tools,'--no-save','--no-package-lock',"pnpm@$($config.pnpm)")
        $env:Path = (Join-Path $tools 'node_modules/.bin')+';'+$env:Path
    }
    $venvPython = Join-Path $repo '.venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Run-Checked -Program $Python -Arguments @('-B','-m','venv',(Join-Path $repo '.venv'))
    }
    Run-Checked -Program $venvPython -Arguments @('-B',(Join-Path $repo 'scripts/build_release.py'),'--output',$Output,'--download-cache',$DownloadCache)
    Write-Host ''
    Write-Host "Ready: $Output\FusionLab.exe"
    Write-Host "Share: $Output.zip"
    Write-Host 'Double-click FusionLab.exe. Keep python and resources beside it. WebView2 Runtime is required.'
}
finally {
    $env:Path = $previousPath
    $env:RUSTUP_TOOLCHAIN = $previousRust
    $env:PYTHONDONTWRITEBYTECODE = $previousBytecode
}
