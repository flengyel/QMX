# Ensure-FT8-TimeSync.ps1
# Purpose: keep Windows time usable for FT8/WSJT-X after rebuild/reboot.

$ErrorActionPreference = "Stop"

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
    Write-Host "ERROR: Run this script from PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "Configuring Windows Time service..."

Set-Service w32time -StartupType Automatic

if ((Get-Service w32time).Status -ne "Running") {
    Start-Service w32time
}

# Configure normal NTP client mode for a standalone Windows 11 PC.
w32tm /config `
    /manualpeerlist:"time.windows.com,0x8 time.nist.gov,0x8 pool.ntp.org,0x8" `
    /syncfromflags:manual `
    /update | Out-Host

Restart-Service w32time
Start-Sleep -Seconds 3

Write-Host "`nForcing time resync..."
w32tm /resync /force | Out-Host

Write-Host "`nWindows Time status:"
w32tm /query /status | Out-Host

Write-Host "`nOffset check against time.windows.com:"
w32tm /stripchart /computer:time.windows.com /samples:5 /dataonly | Out-Host

Write-Host "`nDone. For FT8, offsets should be well under +/-1 second."