param([Parameter(Mandatory=$true)][string]$Executable, [Parameter(Mandatory=$true)][string]$DataDir)
$ErrorActionPreference = 'Stop'
$desktopExecutable = (Resolve-Path -LiteralPath $Executable).Path
$desktopData = Join-Path ([IO.Path]::GetFullPath($DataDir)) ('run-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $desktopData -Force | Out-Null
$previousData = $env:FUSIONLAB_DATA_DIR
$desktopProcess = $null
try {
    $env:FUSIONLAB_DATA_DIR = $desktopData
    $desktopProcess = Start-Process -FilePath $desktopExecutable -ArgumentList '--smoke-test' -PassThru -WindowStyle Hidden
    $deadline = [DateTime]::UtcNow.AddSeconds(25)
    $ready = $null
    while ([DateTime]::UtcNow -lt $deadline -and !$desktopProcess.HasExited) {
        $ready = Get-ChildItem -LiteralPath $desktopData -Filter 'backend-*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($ready) { break }
        Start-Sleep -Milliseconds 100
        $desktopProcess.Refresh()
    }
    if (!$ready) { throw 'Native desktop did not create backend readiness file; inspect backend.log.' }
    $connection = Get-Content -LiteralPath $ready.FullName -Raw | ConvertFrom-Json
    $uri = [Uri]$connection.url
    if ($uri.Host -ne '127.0.0.1') { throw 'Backend must bind loopback.' }
    $response = Invoke-WebRequest -Uri ($connection.url + '/api/platform/info') -SkipHttpErrorCheck
    if ($response.StatusCode -ne 401) { throw 'Native session authentication was not enforced.' }
    $backendPid = (Get-NetTCPConnection -LocalPort $uri.Port -State Listen).OwningProcess
    $desktopProcess.Kill()
    $desktopProcess.WaitForExit()
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while ((Get-Process -Id $backendPid -ErrorAction SilentlyContinue) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 100 }
    if (Get-Process -Id $backendPid -ErrorAction SilentlyContinue) { throw 'Python backend survived desktop process termination.' }
    Write-Output 'Native desktop started Python; random loopback port and auth verified; Windows Job Object terminated backend.'
} finally {
    if ($desktopProcess -and !$desktopProcess.HasExited) { $desktopProcess.Kill(); $desktopProcess.WaitForExit() }
    $env:FUSIONLAB_DATA_DIR = $previousData
}
