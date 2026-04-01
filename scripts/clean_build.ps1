param(
    [switch]$PauseAtEnd = $true
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Split-Path -Parent $scriptDir

    Set-Location $repoRoot

    Write-Step "Cleaning previous build artifacts"

    if (Test-Path "build") {
        Remove-Item -Recurse -Force "build"
        Write-Host "Removed build/" -ForegroundColor Yellow
    }

    if (Test-Path "dist") {
        Remove-Item -Recurse -Force "dist"
        Write-Host "Removed dist/" -ForegroundColor Yellow
    }

    Get-ChildItem -Path $repoRoot -Filter *.spec | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "Removed $($_.Name)" -ForegroundColor Yellow
    }

    Write-Step "Running build"
    python "$repoRoot\scripts\build_windows.py"

    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE"
    }

    Write-Step "Build finished successfully"
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

if ($PauseAtEnd) {
    Write-Host ""
    Pause
}