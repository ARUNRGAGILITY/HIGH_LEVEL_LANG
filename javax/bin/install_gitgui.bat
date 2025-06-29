@echo off
setlocal enabledelayedexpansion

set INSTALL_DIR=%ProgramFiles%\GitGUI
set USER_INSTALL_DIR=%USERPROFILE%\AppData\Local\GitGUI

echo Git GUI Installer
echo =================

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Installing Git GUI system-wide to: %INSTALL_DIR%
    set TARGET_DIR=%INSTALL_DIR%
    set SYSTEM_INSTALL=1
) else (
    echo Installing Git GUI for current user to: %USER_INSTALL_DIR%
    set TARGET_DIR=%USER_INSTALL_DIR%
    set SYSTEM_INSTALL=0
)

:: Create target directory
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

:: Copy files
copy git_gui.py "%TARGET_DIR%\" >nul
copy git-gui.bat "%TARGET_DIR%\" >nul

:: Create a wrapper batch file
echo @echo off > "%TARGET_DIR%\git-gui-launcher.bat"
echo cd /d "%TARGET_DIR%" >> "%TARGET_DIR%\git-gui-launcher.bat"
echo call git-gui.bat %%* >> "%TARGET_DIR%\git-gui-launcher.bat"

:: Add to PATH
if %SYSTEM_INSTALL% == 1 (
    :: System-wide installation - add to system PATH
    setx PATH "%PATH%;%TARGET_DIR%" /M >nul 2>&1
    if %errorlevel% == 0 (
        echo Added to system PATH successfully
    ) else (
        echo Warning: Could not add to system PATH automatically
        echo Please add %TARGET_DIR% to your system PATH manually
    )
) else (
    :: User installation - add to user PATH
    setx PATH "%PATH%;%TARGET_DIR%" >nul 2>&1
    if %errorlevel% == 0 (
        echo Added to user PATH successfully
    ) else (
        echo Warning: Could not add to user PATH automatically
        echo Please add %TARGET_DIR% to your PATH manually
    )
)

echo.
echo Installation completed successfully!
echo You can now run 'git-gui-launcher' from anywhere
echo or run 'git-gui.bat' from the installation directory
echo.
pause