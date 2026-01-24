# PySpring Project Quick Start Script (Local Install)
# Usage:
#   .\init-pyspring-project-local.ps1                          # Create pyspring-demo in current directory
#   .\init-pyspring-project-local.ps1 my-project               # Create my-project in current directory
#   .\init-pyspring-project-local.ps1 my-project D:\Projects   # Create my-project in specified directory

param(
    [string]$ProjectName = "pyspring-demo",
    [string]$BasePath = $PWD,
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
Write-Host "   PySpring Project Initialization (Local)" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

try {
    # Get PySpring source directory (where this script is located)
    $PySpringSourcePath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Write-Info "PySpring source path: $PySpringSourcePath"

    Write-Step "1/8" "Check Dependencies"
    
    if (-not (Test-CommandExists "uv")) {
        Write-Err "uv not installed! Please install:"
        Write-Host "  Method 1: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
        Write-Host "  Method 2: pip install uv"
        exit 1
    }
    Write-Success "uv installed"
    
    if (-not (Test-CommandExists "python")) {
        Write-Err "Python not installed! Please install Python 3.10+"
        exit 1
    }
    $pythonVersion = python --version
    Write-Success "$pythonVersion"

    Write-Step "2/8" "Prepare PySpring Source"
    
    Write-Info "Using editable install from: $PySpringSourcePath"
    Write-Success "Source path verified"

    Write-Step "3/8" "Create Project Directory"
    
    $ProjectPath = Join-Path $BasePath $ProjectName
    
    if (Test-Path $ProjectPath) {
        Write-Host "WARNING: Project directory already exists: " -NoNewline -ForegroundColor Yellow
        Write-Host "$ProjectPath" -ForegroundColor Cyan
        Write-Host ""
        $response = Read-Host "Delete and recreate? (y/N)"
        Write-Host ""
        
        if ($response -eq "y" -or $response -eq "Y") {
            Write-Info "Clearing existing directory contents..."
            
            # 检查当前工作目录是否在要清空的目录内
            $currentPath = $PWD.Path
            $needReturnToProject = $false
            if ($currentPath.StartsWith($ProjectPath)) {
                Write-Info "Current directory is inside target, switching to parent..."
                $parentPath = Split-Path -Parent $ProjectPath
                Push-Location $parentPath
                $needReturnToProject = $true
            }
            
            # 尝试释放可能被占用的文件句柄
            [System.GC]::Collect()
            [System.GC]::WaitForPendingFinalizers()
            
            # 尝试清空目录内容（而不是删除目录本身）
            $maxRetries = 3
            $retryCount = 0
            $cleared = $false
            
            while (-not $cleared -and $retryCount -lt $maxRetries) {
                try {
                    # 删除目录内的所有内容，但保留目录本身
                    Get-ChildItem -Path $ProjectPath -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction Stop
                    $cleared = $true
                    Write-Success "Directory contents cleared"
                    
                    # 如果之前切换了目录，现在切换回去
                    if ($needReturnToProject) {
                        Pop-Location
                        Set-Location $ProjectPath
                    }
                } catch {
                    $retryCount++
                    if ($retryCount -lt $maxRetries) {
                        Write-Host "Directory is in use, retrying in 2 seconds... (Attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
                        Start-Sleep -Seconds 2
                    } else {
                        Write-Host ""
                        Write-Err "Failed to clear directory after $maxRetries attempts"
                        Write-Host ""
                        Write-Host "Common causes:" -ForegroundColor Yellow
                        Write-Host "  1. Virtual environment is activated in another terminal" -ForegroundColor White
                        Write-Host "     Solution: Run 'deactivate' in all terminals, or close them" -ForegroundColor Gray
                        Write-Host "  2. VS Code has opened files from this directory" -ForegroundColor White
                        Write-Host "     Solution: Close VS Code workspace/folder" -ForegroundColor Gray
                        Write-Host "  3. File explorer or other programs are accessing this directory" -ForegroundColor White
                        Write-Host "     Solution: Close all related windows" -ForegroundColor Gray
                        Write-Host ""
                        Write-Host "Try: Close all programs accessing this directory and run again" -ForegroundColor Yellow
                        if ($needReturnToProject) {
                            Pop-Location
                        }
                        exit 1
                    }
                }
            }
        } else {
            Write-Info "Installation cancelled by user"
            exit 0
        }
    }
    
    # 创建或确认项目目录存在
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

    Write-Step "4/8" "Create Virtual Environment"
    
    Push-Location $ProjectPath
    
    uv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to create virtual environment"
        Pop-Location
        exit 1
    }
    Write-Success "Virtual environment created: $ProjectPath\.venv"

    Write-Step "5/8" "Install PySpring (Editable Mode)"
    
    $venvActivate = Join-Path $ProjectPath ".venv\Scripts\Activate.ps1"
    
    if (-not (Test-Path $venvActivate)) {
        Write-Err "Virtual environment activation script not found"
        Pop-Location
        exit 1
    }
    
    & $venvActivate
    
    Write-Info "Installing dependencies from PyPI..."
    uv pip install fastapi uvicorn python-multipart pydantic pydantic-settings dependency_injector loguru pyyaml python-dotenv cryptography sqlalchemy alembic asyncpg aiosqlite redis python-jose passlib fastapi-users
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Failed to install dependencies"
        Pop-Location
        exit 1
    }
    
    Write-Info "Installing PySpring in editable mode from: $PySpringSourcePath"
    uv pip install -e $PySpringSourcePath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "PySpring installation failed"
        Pop-Location
        exit 1
    }
    Write-Success "PySpring installed in editable mode (changes will be reflected immediately)"

    Write-Step "6/8" "Verify Installation"
    
    $pythonExe = Join-Path $ProjectPath ".venv\Scripts\python.exe"
    $pyspringExe = Join-Path $ProjectPath ".venv\Scripts\pyspring.exe"
    
    # Verify by checking if pyspring executable exists
    if (Test-Path $pyspringExe) {
        Write-Success "PySpring CLI installed successfully"
        
        # Try to get version from CLI
        try {
            $cliOutput = & $pyspringExe --version 2>&1 | Out-String
            $versionMatch = [regex]::Match($cliOutput, 'PySpring (\d+\.\d+\.\d+(?:b\d+)?)')
            if ($versionMatch.Success) {
                Write-Info "PySpring version: $($versionMatch.Groups[1].Value)"
            } else {
                Write-Info "PySpring version: installed (editable mode)"
            }
        } catch {
            Write-Info "PySpring CLI installed (version check skipped)"
        }
    } else {
        Write-Host "WARNING: PySpring CLI not found" -ForegroundColor Yellow
    }

    if (-not $SkipExample) {
        Write-Step "7/8" "Create Example Project"
        
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

    Write-Step "8/8" "Installation Complete"
    
    Pop-Location
    
    Write-Host "`n============================================" -ForegroundColor Green
    Write-Host "  Installation Success! (Editable Mode)" -ForegroundColor Green
    Write-Host "============================================`n" -ForegroundColor Green

    Write-Host "Project Path: " -NoNewline
    Write-Host "$ProjectPath" -ForegroundColor Cyan
    
    Write-Host "PySpring Source: " -NoNewline
    Write-Host "$PySpringSourcePath" -ForegroundColor Cyan
    
    Write-Host "`n" -NoNewline
    Write-Host "ℹ️  Editable Mode: " -ForegroundColor Yellow -NoNewline
    Write-Host "Any changes to PySpring source will be immediately available!"
    
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
    Write-Host "  https://github.com/365tools/PySpring`n"

} catch {
    Write-Err "Script execution failed: $_"
    Write-Host $_.ScriptStackTrace
    Pop-Location -ErrorAction SilentlyContinue
    exit 1
}
