@echo off
title AI Usage Dashboard
echo ============================================
echo   AI Usage Dashboard
echo ============================================
echo.

:: Absolute project root
set "PROJECT_DIR=C:\Users\lvona\src\ai-usage-dash"

:: Check for uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: uv not found. Install with: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

:: Parse arguments
set "MODE=gui"
set "EXTRA_ARGS="

:parse_args
if "%~1"=="" goto check_mode
if /i "%~1"=="--browser" set "MODE=browser" & shift & goto parse_args
if /i "%~1"=="-b"        set "MODE=browser" & shift & goto parse_args
if /i "%~1"=="--debug"   set "EXTRA_ARGS=%EXTRA_ARGS% --debug" & shift & goto parse_args
shift
goto parse_args

:check_mode
if "%MODE%"=="browser" goto start_browser

:: Default: try GUI mode
echo Starting desktop app...
echo.
uv run --project "%PROJECT_DIR%" ai-dash --daemon %EXTRA_ARGS%
if %errorlevel% neq 0 (
    echo.
    echo Desktop mode failed - falling back to browser mode...
    echo.
    goto start_browser
)
goto :eof

:start_browser
echo Starting in browser mode...
echo Dashboard: http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.
uv run --project "%PROJECT_DIR%" ai-dash-browser %EXTRA_ARGS%
