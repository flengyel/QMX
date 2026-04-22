# Ensure-FT8-TimeSync.ps1
# Purpose: keep Windows time usable for FT8/WSJT-X after rebuild/reboot.
#
# Supports -WhatIf for a dry run that prints the intended changes without
# applying them. Supports -Confirm for per-change confirmation.

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param()

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

# Declare intent before changing anything. Makes rollback decisions possible
# and gives the operator a chance to bail out before state is mutated.
Write-Host "This script will modify the following Windows Time state:"
Write-Host "  - w32time service startup type: -> Automatic"
Write-Host "  - w32time service state:        -> Running"
Write-Host "  - NTP peer list:                -> time.windows.com,"
Write-Host "                                     time.nist.gov,"
Write-Host "                                     pool.ntp.org"
Write-Host "  - Sync source flag:             -> manual"
Write-Host "  - w32time service:              -> Restart"
Write-Host "  - Force resync:                 -> Yes"
Write-Host ""
Write-Host "Read-only checks after the above:"
Write-Host "  - w32tm /query /status"
Write-Host "  - w32tm /stripchart against time.windows.com"
Write-Host ""

if ($WhatIfPreference) {
    Write-Host "Dry run (-WhatIf): nothing will be changed." -ForegroundColor Yellow
    Write-Host ""
}

if ($PSCmdlet.ShouldProcess("w32time service", "Set startup to Automatic and ensure running")) {
    Set-Service w32time -StartupType Automatic
    if ((Get-Service w32time).Status -ne "Running") {
        Start-Service w32time
    }
}

if ($PSCmdlet.ShouldProcess("w32time configuration",
        "Set NTP peer list and syncfromflags=manual")) {
    w32tm /config `
        /manualpeerlist:"time.windows.com,0x8 time.nist.gov,0x8 pool.ntp.org,0x8" `
        /syncfromflags:manual `
        /update | Out-Host
}

if ($PSCmdlet.ShouldProcess("w32time service", "Restart to pick up configuration")) {
    Restart-Service w32time
    Start-Sleep -Seconds 3
}

if ($PSCmdlet.ShouldProcess("Windows time", "Force resync against configured NTP peers")) {
    Write-Host "`nForcing time resync..."
    w32tm /resync /force | Out-Host
}

# Read-only checks; safe even in WhatIf mode, but skip to keep the dry-run
# output minimal.
if (-not $WhatIfPreference) {
    Write-Host "`nWindows Time status:"
    w32tm /query /status | Out-Host

    Write-Host "`nOffset check against time.windows.com:"
    w32tm /stripchart /computer:time.windows.com /samples:5 /dataonly | Out-Host

    Write-Host "`nDone. For FT8, offsets should be well under +/-1 second."
}
