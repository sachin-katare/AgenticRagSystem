param(
    [string]$OutputDirectory = "docs\output-evidence\submission",
    [switch]$IncludeLocalRunbooks
)

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptPath "..")
$resolvedOutputDirectory = Join-Path $projectRoot $OutputDirectory

New-Item -ItemType Directory -Force -Path $resolvedOutputDirectory | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipPath = Join-Path $resolvedOutputDirectory "AgenticRagSystem_Submission_$timestamp.zip"
$stagingRoot = Join-Path $resolvedOutputDirectory "staging_$timestamp"

Get-ChildItem -LiteralPath $resolvedOutputDirectory -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "staging_*" } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

$includePaths = @(
    "README.md",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "requirements-resolved.txt",
    "app",
    "data",
    "logs",
    "docs",
    "sample_data",
    "scripts",
    "tests"
)

$excludedPathParts = @(
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    "tmp",
    "logs",
    "data\chroma",
    "data\uploads",
    "docs\output-evidence\submission"
)

$excludedAnySegmentParts = @(
    "__pycache__"
)

$excludedFileNames = @(
    ".env",
    "document_catalogue.json"
)

$preservedPlaceholderFiles = @(
    "logs\.gitkeep",
    "data\chroma\.gitkeep",
    "data\uploads\.gitkeep"
)

$excludedExtensions = @(
    ".pyc",
    ".pyo"
)

if (-not $IncludeLocalRunbooks) {
    $excludedFileNames += @(
        "AgenticRagSystem_Commands.md",
        "AgenticRagSystem_Operations.md",
        "AgenticRagSystem_Plan.md"
    )
}

function Test-IsExcluded {
    param([string]$RelativePath)

    $normalizedPath = $RelativePath -replace "/", "\"
    $fileName = Split-Path -Leaf $normalizedPath
    $extension = [System.IO.Path]::GetExtension($fileName)
    $pathSegments = $normalizedPath.Split('\')

    if ($preservedPlaceholderFiles -contains $normalizedPath) {
        return $false
    }

    if ($excludedFileNames -contains $fileName) {
        return $true
    }

    if ($excludedExtensions -contains $extension) {
        return $true
    }

    foreach ($excludedPart in $excludedPathParts) {
        if ($normalizedPath -eq $excludedPart -or $normalizedPath.StartsWith("$excludedPart\")) {
            return $true
        }
    }

    foreach ($excludedPart in $excludedAnySegmentParts) {
        if ($pathSegments -contains $excludedPart) {
            return $true
        }
    }

    return $false
}

function Get-RelativePathCompat {
    param(
        [string]$BasePath,
        [string]$TargetPath
    )

    $resolvedBase = [System.IO.Path]::GetFullPath($BasePath)
    $resolvedTarget = [System.IO.Path]::GetFullPath($TargetPath)

    if (-not $resolvedBase.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $resolvedBase += [System.IO.Path]::DirectorySeparatorChar
    }

    $baseUri = New-Object System.Uri($resolvedBase)
    $targetUri = New-Object System.Uri($resolvedTarget)
    $relativeUri = $baseUri.MakeRelativeUri($targetUri)

    return [System.Uri]::UnescapeDataString($relativeUri.ToString()).Replace('/', '\')
}

try {
    foreach ($includePath in $includePaths) {
        $sourcePath = Join-Path $projectRoot $includePath
        if (-not (Test-Path $sourcePath)) {
            continue
        }

        Get-ChildItem -LiteralPath $sourcePath -Recurse -Force | ForEach-Object {
            if ($_.PSIsContainer) {
                return
            }

            $relativePath = Get-RelativePathCompat -BasePath $projectRoot -TargetPath $_.FullName
            if (Test-IsExcluded $relativePath) {
                return
            }

            $destinationPath = Join-Path $stagingRoot $relativePath
            $destinationDirectory = Split-Path -Parent $destinationPath
            New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $destinationPath
        }
    }

    Compress-Archive -Path (Join-Path $stagingRoot "*") -DestinationPath $zipPath
}
finally {
    if (Test-Path $stagingRoot) {
        Remove-Item -LiteralPath $stagingRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Created submission ZIP:"
Write-Host $zipPath
Write-Host ""
Write-Host "Excluded runtime/private content:"
Write-Host "- .venv, .git, .idea, tmp, logs"
Write-Host "- .env"
Write-Host "- data/chroma, data/uploads, data/document_catalogue.json"
Write-Host "- local runbooks unless -IncludeLocalRunbooks is provided"
