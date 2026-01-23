@echo off
REM Smart publish script for TestPyPI with auto version increment
cd /d %~dp0

echo.
echo ============================================
echo   PySpring TestPyPI Smart Upload
echo ============================================
echo.

echo [1/5] Auto-incrementing version...
powershell -ExecutionPolicy Bypass -File "%~dp0bump-version.ps1"
if errorlevel 1 (
    echo.
    echo ERROR: Failed to bump version
    pause
    exit /b 1
)
echo      Done!

echo.
echo [2/5] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
echo      Done!

echo.
echo [3/5] Building source distribution...
python setup.py sdist
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Make sure setuptools is installed: uv pip install --system setuptools
    pause
    exit /b 1
)
echo      Done!

echo.
echo [4/5] Checking build artifacts...
for %%f in (dist\*.tar.gz) do (
    echo      Built: %%~nxf (%%~zf bytes^)
)
echo.

echo [5/5] Uploading to TestPyPI...
dir dist
echo.

echo [4/4] Uploading to TestPyPI...
python -m twine upload --repository testpypi dist\*.tar.gz
if errorlevel 1 (
    echo.
    echo ERROR: Upload failed!
    echo Check your .pypirc configuration in %USERPROFILE%
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SUCCESS! Package uploaded to TestPyPI
echo ============================================
echo.
echo View at: https://test.pypi.org/project/pyspring/
echo.
echo Install with:
echo   uv pip install --index-url https://test.pypi.org/simple/ pyspring
echo.
pause
