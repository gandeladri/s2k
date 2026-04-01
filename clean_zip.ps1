# clean_zip.ps1
# Creates a lightweight ZIP package from the project root using an allowlist approach.

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$zipName = "s2k_clean.zip"
$tempFolder = Join-Path $projectRoot "_zip_temp"

# File patterns to include
$includePatterns = @(
    "*.py",
    "*.ico",
    "*.spec",
    "*.txt",
    "*.md",
    "*.json",
    "*.yml",
    "*.yaml"
)

# Folders to exclude completely
$excludeFolders = @(
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    ".idea",
    ".vscode"
)

# Files to exclude by name or extension
$excludeFilePatterns = @(
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.zip"
)

function Test-IsExcludedFolder {
    param (
        [string]$FullPath
    )

    foreach ($folder in $excludeFolders) {
        if ($FullPath -match [regex]::Escape("\$folder\")) {
            return $true
        }
    }

    return $false
}

function Test-IsExcludedFile {
    param (
        [System.IO.FileInfo]$File
    )

    foreach ($pattern in $excludeFilePatterns) {
        if ($File.Name -like $pattern) {
            return $true
        }
    }

    return $false
}

# Cleanup previous outputs
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

if (Test-Path $tempFolder) {
    Remove-Item $tempFolder -Recurse -Force
}

New-Item -ItemType Directory -Path $tempFolder | Out-Null

# Collect files using allowlist
$files = Get-ChildItem -Path $projectRoot -Recurse -File -Include $includePatterns | Where-Object {
    -not (Test-IsExcludedFolder $_.FullName) -and
    -not (Test-IsExcludedFile $_)
}

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($projectRoot.Length).TrimStart('\')
    $destinationPath = Join-Path $tempFolder $relativePath
    $destinationDir = Split-Path -Parent $destinationPath

    if (-not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }

    Copy-Item $file.FullName $destinationPath -Force
}

Compress-Archive -Path (Join-Path $tempFolder '*') -DestinationPath $zipName -Force

# Remove temp folder after zip creation
Remove-Item $tempFolder -Recurse -Force

Write-Host "Clean ZIP created successfully: $zipName"