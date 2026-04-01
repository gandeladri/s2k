param(
    [switch]$PauseAtEnd = $true
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

function Fail($message) {
    Write-Host ""
    Write-Host "ERROR: $message" -ForegroundColor Red
    if ($PauseAtEnd) {
        Write-Host ""
        Pause
    }
    exit 1
}

try {
    Write-Step "Checking Python"
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail "Python was not found in PATH."
    }
    Write-Host $pythonVersion -ForegroundColor Green

    Write-Step "Upgrading pip"
    & python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to upgrade pip."
    }

    Write-Step "Installing WinRT packages"
    & python -m pip install `
        winrt-runtime `
        winrt-Windows.Foundation `
        winrt-Windows.Foundation.Collections `
        winrt-Windows.Media.SpeechSynthesis `
        winrt-Windows.Storage.Streams
    if ($LASTEXITCODE -ne 0) {
        Fail "Failed to install one or more WinRT packages."
    }

    Write-Step "Done"
    Write-Host "WinRT TTS dependencies installed successfully." -ForegroundColor Green
}
catch {
    Fail $_.Exception.Message
}

if ($PauseAtEnd) {
    Write-Host ""
    Pause
}
