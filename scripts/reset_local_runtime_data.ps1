param(
    [switch]$Force,
    [switch]$AllowRunningApi
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$dataRoot = Join-Path $projectRoot "data"
$chromaRoot = Join-Path $dataRoot "chroma"
$uploadsRoot = Join-Path $dataRoot "uploads"
$catalogueFile = Join-Path $dataRoot "document_catalogue.json"

Write-Host "Project root: $projectRoot"
Write-Host "This will reset local runtime data only:"
Write-Host " - $chromaRoot"
Write-Host " - $uploadsRoot"
Write-Host " - $catalogueFile"
Write-Host ""
Write-Host "It will not delete source code, tests, sample_data, requirements, or Markdown notes."
Write-Host "Stop the FastAPI/Uvicorn API before running this script."
Write-Host ""

$runningApiProcesses = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and
        $_.CommandLine.Contains("uvicorn") -and
        $_.CommandLine.Contains("app.api.main")
    }

if ($runningApiProcesses -and -not $AllowRunningApi) {
    Write-Host "FastAPI/Uvicorn appears to be running."
    Write-Host "Stop the API with Ctrl+C, then run this script again."
    Write-Host "Reason: the running API keeps the document catalogue in memory and may write old records back to JSON."
    exit 1
}

if (-not $Force) {
    $confirmation = Read-Host "Type RESET to continue"
    if ($confirmation -ne "RESET") {
        Write-Host "Reset cancelled."
        exit 0
    }
}

New-Item -ItemType Directory -Force -Path $chromaRoot | Out-Null
New-Item -ItemType Directory -Force -Path $uploadsRoot | Out-Null

Get-ChildItem -LiteralPath $chromaRoot -Force |
    Where-Object { $_.Name -ne ".gitkeep" } |
    Remove-Item -Recurse -Force

Get-ChildItem -LiteralPath $uploadsRoot -Force |
    Where-Object { $_.Name -ne ".gitkeep" } |
    Remove-Item -Recurse -Force

if (Test-Path -LiteralPath $catalogueFile) {
    Remove-Item -LiteralPath $catalogueFile -Force
}

if (Test-Path -LiteralPath $catalogueFile) {
    throw "Document catalogue still exists after reset: $catalogueFile"
}

New-Item -ItemType File -Force -Path (Join-Path $chromaRoot ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $uploadsRoot ".gitkeep") | Out-Null

Write-Host ""
Write-Host "Local runtime data reset complete."
Write-Host "Next steps:"
Write-Host " 1. Restart the FastAPI app."
Write-Host " 2. Re-upload sample documents."
Write-Host " 3. Re-test /search and /ask."
