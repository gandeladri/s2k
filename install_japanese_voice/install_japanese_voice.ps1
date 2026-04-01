# ==========================================
# S2K - Install Japanese Language + TTS
# Auto-elevates to Administrator
# ==========================================

# Check admin
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)

if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow

    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "=== Installing Japanese language and TTS ===" -ForegroundColor Cyan

$capabilities = @(
    "Language.Basic~~~ja-JP~0.0.1.0",
    "Language.Speech~~~ja-JP~0.0.1.0",
    "Language.TextToSpeech~~~ja-JP~0.0.1.0"
)

foreach ($cap in $capabilities) {
    $status = (Get-WindowsCapability -Online | Where-Object Name -eq $cap)

    if ($status.State -eq "Installed") {
        Write-Host "[OK] $cap already installed" -ForegroundColor Green
    } else {
        Write-Host "[INSTALLING] $cap ..." -ForegroundColor Yellow
        try {
            Add-WindowsCapability -Online -Name $cap -ErrorAction Stop
            Write-Host "[OK] $cap installed" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Failed to install $cap" -ForegroundColor Red
            Write-Host $_
        }
    }
}

Write-Host ""
Write-Host "Done. You may need to restart Windows." -ForegroundColor Cyan
Pause