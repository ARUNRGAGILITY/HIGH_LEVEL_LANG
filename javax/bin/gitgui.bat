@echo off
setlocal

:: Set script directory
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%git_gui.py

:: Check if Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo Error: git_gui.py not found in %SCRIPT_DIR%
    echo Please ensure git_gui.py is in the same directory as this batch file.
    pause
    exit /b 1
)

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.x and ensure it's in your system PATH
    pause
    exit /b 1
)

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Git is not installed or not in PATH
    echo Please install Git and ensure it's in your system PATH
    pause
    exit /b 1
)

:: Check if we're in a git repository
if "%1"=="" (
    if exist ".git" (
        echo Starting Git GUI in current directory: %CD%
    ) else (
        echo Starting Git GUI - you can browse to select a repository
    )
) else (
    if exist "%1\.git" (
        echo Starting Git GUI in directory: %1
        cd /d "%1"
    ) else (
        echo Warning: %1 does not appear to be a git repository
        echo Starting Git GUI anyway - you can browse to select a repository
        if exist "%1" cd /d "%1"
    )
)

echo.
echo Launching Python Git GUI...
echo Press Ctrl+C to exit
echo.

:: Run the Python script
python "%PYTHON_SCRIPT%"

if %errorlevel% neq 0 (
    echo.
    echo Git GUI exited with error code: %errorlevel%
    pause
)

endlocal
