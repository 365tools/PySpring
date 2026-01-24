@echo off
REM Install PySpring from local source for development/testing
cd /d %~dp0

echo.
echo ============================================
echo   PySpring Local Installation
echo ============================================
echo.

echo [1/4] Auto-incrementing version...
powershell -ExecutionPolicy Bypass -File "%~dp0bump-version.ps1"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to bump version
    pause
    exit /b 1
)
echo      Done!

echo.
echo [2/4] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist src\pyspring.egg-info rmdir /s /q src\pyspring.egg-info
echo      Done!

echo.
echo [3/4] Building distribution...
python setup.py sdist bdist_wheel
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Make sure setuptools and wheel are installed:
    echo   uv pip install --system setuptools wheel
    pause
    exit /b 1
)
echo      Done!

echo.
echo [4/4] Installing from local build...
for %%f in (dist\*.whl) do (
    echo      Installing: %%~nxf
    uv pip install --force-reinstall "%%f"
    if errorlevel 1 (
        echo.
        echo ERROR: Installation failed!
        pause
        exit /b 1
    )
)
echo      Done!

echo.
echo ============================================
echo   SUCCESS! PySpring installed from local
echo ============================================
echo.
echo Installed version:
python -c "import pyspring; print(f'  PySpring v{pyspring.__version__}')" 2>nul
if errorlevel 1 (
    echo   [Unable to determine version]
)
echo.
echo You can now test the framework with:
echo   pyspring --version
echo   pyspring init --example
echo.
pause
