$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$logsDirectory = Join-Path $projectRoot "logs"

Write-Host "This will clear local log files under:"
Write-Host $logsDirectory
Write-Host ""
Write-Host "It will remove app.log, error.log, and rotated log files only."
Write-Host "It will not remove uploads, ChromaDB data, the document catalogue, or source code."
Write-Host ""

$confirmation = Read-Host "Type CLEAR_LOGS to continue"
if ($confirmation -ne "CLEAR_LOGS") {
    Write-Host "Cancelled. No log files were removed."
    exit 0
}

if (-not (Test-Path $logsDirectory)) {
    Write-Host "Logs directory does not exist. Nothing to clear."
    exit 0
}

$logFiles = Get-ChildItem -LiteralPath $logsDirectory -File |
    Where-Object {
        $_.Name -eq "app.log" -or
        $_.Name -like "app.log.*" -or
        $_.Name -eq "error.log" -or
        $_.Name -like "error.log.*"
    }

if ($logFiles.Count -eq 0) {
    Write-Host "No app or error log files found."
    exit 0
}

foreach ($logFile in $logFiles) {
    Remove-Item -LiteralPath $logFile.FullName -Force
    Write-Host "Removed $($logFile.Name)"
}

Write-Host "Local logs cleared."
