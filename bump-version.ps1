# Smart version bumper for TestPyPI upload (Beta versioning)
# Usage:
#   .\bump-version.ps1              # Bump all packages (default target package: pyspring)
#   .\bump-version.ps1 -Target test # Same as default
#   .\bump-version.ps1 -Target prod # Print a stable version hint
param(
    [ValidateSet('test', 'prod')]
    [string]$Target = 'test'
)

$ErrorActionPreference = "Stop"

Write-Host "`nFetching latest version from TestPyPI..." -ForegroundColor Cyan

# The release package name used for version lookup (aggregate package).
$PackageName = "pyspring"
$newVersion = $null

try {
    $response = Invoke-RestMethod -Uri "https://test.pypi.org/pypi/$PackageName/json" -ErrorAction Stop
    $latestVersion = $response.info.version
    Write-Host "  Current version on TestPyPI: $latestVersion" -ForegroundColor Yellow

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
        $newVersion = "$major.$minor.0b1"
        Write-Host "  Starting new beta cycle: $latestVersion -> $newVersion" -ForegroundColor Cyan
    } else {
        throw "Unexpected version format: $latestVersion"
    }
} catch {
    Write-Host "  WARNING: Could not read TestPyPI version ($($_.Exception.Message))" -ForegroundColor Yellow
    Write-Host "  Using version from root pyproject.toml" -ForegroundColor Yellow
    $rootContent = Get-Content "$PSScriptRoot\pyproject.toml" -Raw
    if ($rootContent -match 'version\s*=\s*"([\d\.b]+)"') {
        $newVersion = $matches[1]
    } else {
        Write-Host "  ERROR: Could not find version in root pyproject.toml" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  New version will be: $newVersion" -ForegroundColor Green
Write-Host ""

if ($Target -eq 'prod') {
    Write-Host "  NOTE: For production releases, drop the 'b' suffix manually (e.g. $newVersion -> $($newVersion -replace 'b\d+$', ''))" -ForegroundColor Yellow
}

# Collect all pyproject.toml files (root + each package)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$pyprojects = @()
$pyprojects += "$PSScriptRoot\pyproject.toml"
Get-ChildItem "$PSScriptRoot\packages" -Directory | ForEach-Object {
    $p = Join-Path $_.FullName "pyproject.toml"
    if (Test-Path $p) { $pyprojects += $p }
}

foreach ($p in $pyprojects) {
    $content = Get-Content $p -Raw -Encoding UTF8
    if ($content -match 'version\s*=\s*"[^"]+"') {
        $content = $content -replace 'version\s*=\s*"[^"]+"', "version = `"$newVersion`""
        [System.IO.File]::WriteAllText($p, $content, $utf8NoBom)
        Write-Host "  Updated: $($p.Replace($PSScriptRoot + '\', ''))" -ForegroundColor Green
    } else {
        Write-Host "  SKIPPED (no version field): $($p.Replace($PSScriptRoot + '\', ''))" -ForegroundColor Yellow
    }
}

Write-Host "`nVersion bump complete! ($(($pyprojects | Measure-Object).Count) pyproject.toml files)`n" -ForegroundColor Cyan
