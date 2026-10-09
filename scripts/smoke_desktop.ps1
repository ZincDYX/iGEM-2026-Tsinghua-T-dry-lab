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
    $deadline = [DateTime]::UtcNow.AddSeconds(75)
    $ready = $false
    $backendPid = $null
    while ([DateTime]::UtcNow -lt $deadline -and !$desktopProcess.HasExited) {
        # Startup now uses the parent IPC pipe, not a backend-*.json file.
        # Inspect only this owned desktop's child and its actual loopback API.
        $child = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.ParentProcessId -eq $desktopProcess.Id } | Select-Object -First 1
        if ($child) {
            $backendPid = [int]$child.ProcessId
            $socket = Get-NetTCPConnection -State Listen -OwningProcess $backendPid -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($socket) {
                if ($socket.LocalAddress -ne '127.0.0.1') { throw 'Backend must bind loopback.' }
                try {
                    $response = Invoke-WebRequest -Uri ('http://127.0.0.1:' + $socket.LocalPort + '/api/platform/info') -SkipHttpErrorCheck -TimeoutSec 2
                    if ($response.StatusCode -ne 401) { throw 'Native session authentication was not enforced.' }
                    $ready = $true
                    break
                } catch [System.Net.Http.HttpRequestException] { }
                  catch [System.Threading.Tasks.TaskCanceledException] { }
            }
        }
        Start-Sleep -Milliseconds 300
        $desktopProcess.Refresh()
    }
    if (!$ready) { throw 'Owned native backend API did not become ready; inspect backend.log.' }
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
