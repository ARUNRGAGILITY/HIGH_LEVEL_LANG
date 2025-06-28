@echo off
REM Pseudo Java Compiler (pjc) - Windows Batch Script
REM Usage: pjc [options] input.pj

setlocal enabledelayedexpansion

REM Set script directory
set SCRIPT_DIR=%~dp0
set PARSER_SCRIPT=%SCRIPT_DIR%pseudo_java_parser.py

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.6+ and add it to your PATH
    exit /b 1
)

REM Check if parser script exists
if not exist "%PARSER_SCRIPT%" (
    echo Error: Parser script not found at %PARSER_SCRIPT%
    echo Please ensure pseudo_java_parser.py is in the same directory as this script
    exit /b 1
)

REM Show help if no arguments
if "%~1"=="" (
    echo Pseudo Java Compiler ^(javax^) - Convert pseudo-Java to Java
    echo.
    echo Usage: javax [options] input.pj
    echo.
    echo Options:
    echo   -o ^<file^>        Output Java file
    echo   --output-dir ^<dir^> Output directory for Java files
    echo   -c, --compile     Compile generated Java code
    echo   -r, --run         Compile and run the generated Java code
    echo   -v, --verbose     Verbose output
    echo   --test            Run built-in test
    echo   --help            Show this help message
    echo   --version         Show version information
    echo.
    echo Examples:
    echo   javax example.pj
    echo   javax example.pj -o Example.java
    echo   javax example.pj --output-dir src\main\java
    echo   javax example.pj -cr
    echo   javax --test
    exit /b 0
)

REM Handle help flag
if "%~1"=="--help" (
    python "%PARSER_SCRIPT%" --help
    exit /b 0
)

REM Handle version flag
if "%~1"=="--version" (
    python "%PARSER_SCRIPT%" --version
    exit /b 0
)

REM Handle test flag
if "%~1"=="--test" (
    echo Running built-in test...
    python "%PARSER_SCRIPT%" --test
    exit /b 0
)

REM Check for Java compiler if compile flags are used
set NEEDS_JAVAC=0
for %%i in (%*) do (
    if "%%i"=="-c" set NEEDS_JAVAC=1
    if "%%i"=="--compile" set NEEDS_JAVAC=1
    if "%%i"=="-r" set NEEDS_JAVAC=1
    if "%%i"=="--run" set NEEDS_JAVAC=1
    if "%%i"=="-cr" set NEEDS_JAVAC=1
    if "%%i"=="-rc" set NEEDS_JAVAC=1
)

if %NEEDS_JAVAC%==1 (
    javac -version >nul 2>&1
    if errorlevel 1 (
        echo Warning: Java compiler ^(javac^) not found in PATH
        echo Compilation features will not work
        echo Please install JDK and add it to your PATH
    )
)

REM Handle combined flags like -cr, -rc
set NEW_ARGS=
for %%i in (%*) do (
    if "%%i"=="-cr" (
        set NEW_ARGS=!NEW_ARGS! --compile --run
    ) else if "%%i"=="-rc" (
        set NEW_ARGS=!NEW_ARGS! --compile --run
    ) else (
        set NEW_ARGS=!NEW_ARGS! %%i
    )
)

REM Execute Python parser with all arguments
echo Pseudo Java Compiler - Processing...
python "%PARSER_SCRIPT%" %NEW_ARGS%

REM Check exit code
if errorlevel 1 (
    echo.
    echo Compilation failed. Use -v for verbose output.
    exit /b 1
) else (
    echo.
    echo Process completed successfully!
    exit /b 0
)