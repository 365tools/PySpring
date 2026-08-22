# PySpring Project Quick Start Script
# Usage:
#   .\init-pyspring-project.ps1                          # Create pyspring-demo in current directory
#   .\init-pyspring-project.ps1 my-project               # Create my-project in current directory
#   .\init-pyspring-project.ps1 my-project D:\Projects   # Create my-project in specified directory

param(
    [string]$ProjectName = "pyspring-demo",
    [string]$BasePath = $PWD,
    [switch]$UseTestPyPI = $false,
    [switch]$SkipExample = $false
)

$ErrorActionPreference = "Stop"

function Write-Info { param($Message) Write-Host "INFO: $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "SUCCESS: $Message" -ForegroundColor Green }
function Write-Err { param($Message) Write-Host "ERROR: $Message" -ForegroundColor Red }
function Write-Step { param($Step, $Message) Write-Host "`n[$Step] $Message" -ForegroundColor Yellow }

function Test-CommandExists {
    param($Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "   PySpring Project Initialization" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

try {
    Write-Step "1/7" "Check Dependencies"
    
    if (-not (Test-CommandExists "uv")) {
        Write-Err "uv not installed! Please install:"
        Write-Host "  Method 1: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        Write-Host "  Method 2: pip install uv"
        exit 1
    }
    Write-Success "uv installed"
    
    if (-not (Test-CommandExists "python")) {
        Write-Err "Python not installed! Please install Python 3.14+"
        exit 1
    }
    $pythonVersion = python --version
    Write-Success "$pythonVersion"

    Write-Step "2/7" "Create Project Directory"
    
    $ProjectPath = Join-Path $BasePath $ProjectName
    
    if (Test-Path $ProjectPath) {
        Write-Host "WARNING: Project directory already exists: " -NoNewline -ForegroundColor Yellow
        Write-Host "$ProjectPath" -ForegroundColor Cyan
        Write-Host ""
        $response = Read-Host "Delete and recreate? (y/N)"
        Write-Host ""
        
        if ($response -eq "y" -or $response -eq "Y") {
            Write-Info "Deleting existing directory..."
            
            # 尝试释放可能被占用的文件句柄
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            
            # 尝试强制删除，添加错误处理和重试逻辑
            $maxRetries = 3
            $retryCount = 0
            $deleted = $false
            
            while (-not $deleted -and $retryCount -lt $maxRetries) {
                try {
                    # 先尝试删除文件内容
                    Get-ChildItem -Path $ProjectPath -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction Stop
                    # 再删除目录本身
                    Remove-Item -Path $ProjectPath -Force -ErrorAction Stop
                    $deleted = $true
                    Write-Success "Old directory deleted"
                } catch {
                    $retryCount++
                    if ($retryCount -lt $maxRetries) {
                        Write-Host "Directory is in use, retrying in 2 seconds... (Attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
                        Start-Sleep -Seconds 2
                    } else {
                        Write-Host ""
                        Write-Err "Failed to delete directory after $maxRetries attempts"
                        Write-Host ""
                        Write-Host "Common causes:" -ForegroundColor Yellow
                        Write-Host "  1. Virtual environment is activated in another terminal" -ForegroundColor White
                        Write-Host "     Solution: Run 'deactivate' in all terminals, or close them" -ForegroundColor Gray
                        Write-Host "  2. VS Code has opened files from this directory" -ForegroundColor White
                        Write-Host "     Solution: Close VS Code workspace/folder" -ForegroundColor Gray
                        Write-Host "  3. File explorer or other programs are accessing this directory" -ForegroundColor White
                        Write-Host "     Solution: Close all related windows" -ForegroundColor Gray
                        Write-Host ""
                        Write-Host "Or manually delete: " -NoNewline -ForegroundColor Yellow
                        Write-Host "$ProjectPath" -ForegroundColor Cyan
                        exit 1
                    }
                }
            }
        } else {
            Write-Info "Installation cancelled by user"
            exit 0
        }
    }
    
    # 创建项目目录
    if (-not (Test-Path $ProjectPath)) {
        try {
            New-Item -ItemType Directory -Path $ProjectPath -ErrorAction Stop | Out-Null
            Write-Success "Project directory created: $ProjectPath"
        } catch {
            Write-Err "Failed to create project directory"
            Write-Host "Error: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Success "Using existing directory: $ProjectPath"
    }

    Write-Step "3/7" "Create Virtual Environment"
    
    Push-Location $ProjectPath
    
    uv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to create virtual environment"
        Pop-Location
        exit 1
    }
    Write-Success "Virtual environment created: $ProjectPath\.venv"

    Write-Step "4/7" "Install PySpring"
    
    $venvActivate = Join-Path $ProjectPath ".venv\Scripts\Activate.ps1"
    
    if (-not (Test-Path $venvActivate)) {
        Write-Err "Virtual environment activation script not found"
        Pop-Location
        exit 1
    }
    
    & $venvActivate
    
    if ($UseTestPyPI) {
        Write-Info "Fetching latest version from TestPyPI..."
        $htmlContent = (Invoke-WebRequest -Uri "https://test.pypi.org/simple/pyspring/" -UseBasicParsing).Content
        $versionList = [regex]::Matches($htmlContent, 'pyspring-([0-9]+\.[0-9]+\.[0-9]+(?:b[0-9]+)?)') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
        
        # Custom sort to get the truly latest version (considering beta numbers)
        $latestVersion = $versionList | Sort-Object -Descending {
            if ($_ -match '^(\d+)\.(\d+)\.(\d+)(?:b(\d+))?$') {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]
                $patch = [int]$matches[3]
                $beta = if ($matches[4]) { [int]$matches[4] } else { 999 }  # Non-beta gets high number
                return ($major * 1000000) + ($minor * 10000) + ($patch * 100) + $beta
            }
            return 0
        } | Select-Object -First 1
        
        if ($latestVersion) {
            Write-Info "Installing PySpring==$latestVersion from TestPyPI..."
            # First install dependencies from PyPI
            Write-Info "Installing dependencies from PyPI..."
            uv pip install fastapi uvicorn python-multipart pydantic pydantic-settings loguru pyyaml python-dotenv cryptography sqlalchemy aiosqlite redis python-jose passlib
            
            # Get the actual download URL from TestPyPI simple API
            Write-Info "Fetching download URL..."
            $packagePattern = "pyspring-$latestVersion\.tar\.gz"
            $downloadUrl = [regex]::Match($htmlContent, "href=`"([^`"]+$packagePattern[^`"]*)`"").Groups[1].Value
            
            if ($downloadUrl) {
                Write-Info "Downloading from: $downloadUrl"
                uv pip install $downloadUrl
            } else {
                Write-Err "Could not find download URL for version $latestVersion"
                Pop-Location
                exit 1
            }
        } else {
            Write-Info "Installing latest PySpring from TestPyPI..."
            uv pip install --index-strategy unsafe-best-match --prerelease=allow --index-url https://pypi.org/simple/ --extra-index-url https://test.pypi.org/simple/ pyspring
        }
    } else {
        Write-Info "Installing from PyPI..."
        uv pip install pyspring
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "PySpring installation failed"
        Pop-Location
        exit 1
    }
    Write-Success "PySpring installed"

    Write-Step "5/7" "Verify Installation"
    
    $pythonExe = Join-Path $ProjectPath ".venv\Scripts\python.exe"
    $pyspringExe = Join-Path $ProjectPath ".venv\Scripts\pyspring.exe"
    
    # Verify by checking if pyspring executable exists (simpler than importing)
    if (Test-Path $pyspringExe) {
        Write-Success "PySpring CLI installed successfully"
        
        # Try to get version from CLI
        try {
            $cliOutput = & $pyspringExe --version 2>&1 | Out-String
            $versionMatch = [regex]::Match($cliOutput, 'PySpring (\d+\.\d+\.\d+(?:b\d+)?)')
            if ($versionMatch.Success) {
                Write-Info "PySpring version: $($versionMatch.Groups[1].Value)"
            } else {
                Write-Info "PySpring version: installed"
            }
        } catch {
            Write-Info "PySpring CLI installed (version check skipped)"
        }
    } else {
        Write-Host "WARNING: PySpring CLI not found" -ForegroundColor Yellow
    }

    if (-not $SkipExample) {
        Write-Step "6/7" "Create Example Project"
        
        $pyspringExe = Join-Path $ProjectPath ".venv\Scripts\pyspring.exe"
        & $pyspringExe init . --example --force
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to create example project"
            Pop-Location
            exit 1
        }
        Write-Success "Example project created"
        
        Write-Info "Installing project dependencies..."
        uv pip install -r requirements.txt
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to install dependencies"
            Pop-Location
            exit 1
        }
        Write-Success "Dependencies installed"
    } else {
        Write-Info "Skipped example project creation"
    }

    Write-Step "7/7" "Installation Complete"
    
    Pop-Location
    
    Write-Host "`n============================================" -ForegroundColor Green
    Write-Host "         Installation Success!" -ForegroundColor Green
    Write-Host "============================================`n" -ForegroundColor Green

    Write-Host "Project Path: " -NoNewline
    Write-Host "$ProjectPath" -ForegroundColor Cyan
    
    Write-Host "`nQuick Start:" -ForegroundColor Yellow
    Write-Host "  cd $ProjectPath"
    
    if (-not $SkipExample) {
        Write-Host "`nRun Example (Method 1 - Direct execution):" -ForegroundColor Yellow
        Write-Host "  .venv\Scripts\uvicorn.exe app.main:app --reload"
        
        Write-Host "`nRun Example (Method 2 - With venv activation):" -ForegroundColor Yellow
        Write-Host "  powershell -ExecutionPolicy Bypass -Command `"& .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload`""
        
        Write-Host "`nAccess:"
        Write-Host "  API:          http://localhost:8000"
        Write-Host "  API Docs:     http://localhost:8000/docs"
        Write-Host "  Health Check: http://localhost:8000/health"
        Write-Host "`nDefault Account:"
        Write-Host "  Username: admin"
        Write-Host "  Password: admin123"
    } else {
        Write-Host "`nCreate App:" -ForegroundColor Yellow
        Write-Host "  .venv\Scripts\pyspring.exe init . --example"
    }
    
    Write-Host "`nDocumentation:" -ForegroundColor Yellow
    Write-Host "  https://github.com/eavelabs-community/py-spring`n"

} catch {
    Write-Err "Script execution failed: $_"
    Write-Host $_.ScriptStackTrace
    Pop-Location -ErrorAction SilentlyContinue
    exit 1
}