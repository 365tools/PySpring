# Smart version bumper for TestPyPI upload (Beta versioning)
param([string]$PackageName = "pyspring")

Write-Host "`nFetching latest version from TestPyPI..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "https://test.pypi.org/pypi/$PackageName/json" -ErrorAction Stop
    $latestVersion = $response.info.version
    Write-Host "  Current version on TestPyPI: $latestVersion" -ForegroundColor Yellow
    
    # Check if latest version is a beta version (e.g., 1.1.0b1)
    if ($latestVersion -match '^(\d+)\.(\d+)\.(\d+)b(\d+)$') {
        # Beta version found, increment beta number
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        $patch = [int]$matches[3]
        $betaNum = [int]$matches[4] + 1
        $newVersion = "$major.$minor.${patch}b$betaNum"
        Write-Host "  Incrementing beta version: $latestVersion -> $newVersion" -ForegroundColor Cyan
    } elseif ($latestVersion -match '^(\d+)\.(\d+)\.(\d+)$') {
        # Stable version found, start new minor version with b1
        $major = [int]$matches[1]
        $minor = [int]$matches[2] + 1
        $patch = 0
        $newVersion = "$major.$minor.${patch}b1"
        Write-Host "  Starting new beta cycle: $latestVersion -> $newVersion" -ForegroundColor Cyan
    } else {
        Write-Host "  WARNING: Unexpected version format: $latestVersion" -ForegroundColor Yellow
        Write-Host "  Using version from pyproject.toml" -ForegroundColor Yellow
        $currentContent = Get-Content pyproject.toml -Raw
        if ($currentContent -match 'version\s*=\s*"([\d\.b]+)"') {
            $newVersion = $matches[1]
        } else {
            Write-Host "  ERROR: Could not find version in pyproject.toml" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  Package not found on TestPyPI, starting with 1.1.0b1" -ForegroundColor Yellow
    $newVersion = "1.1.0b1"
}

Write-Host "  New version will be: $newVersion" -ForegroundColor Green
Write-Host ""

# Update pyproject.toml
$pyprojectContent = Get-Content pyproject.toml -Raw -Encoding UTF8
$pyprojectContent = $pyprojectContent -replace 'version\s*=\s*"[\d\.b]+"', "version = ""$newVersion"""
$pyprojectContent = $pyprojectContent -replace 'version\s*=\s*\\"[\d\.b]+"', "version = ""$newVersion"""
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("$PSScriptRoot\pyproject.toml", $pyprojectContent, $utf8NoBom)
Write-Host "  Updated pyproject.toml" -ForegroundColor Green

# Update setup.py
$setupContent = Get-Content setup.py -Raw -Encoding UTF8
$setupContent = $setupContent -replace 'version="[\d\.b]+"', "version=""$newVersion"""
$setupContent = $setupContent -replace 'version=\\"[\d\.b]+"', "version=""$newVersion"""
[System.IO.File]::WriteAllText("$PSScriptRoot\setup.py", $setupContent, $utf8NoBom)
Write-Host "  Updated setup.py" -ForegroundColor Green

Write-Host "`nVersion bump complete!`n" -ForegroundColor Cyan
