@echo off
REM Build script for Windows executable

echo ========================================
echo Building AI Usage Dashboard for Windows
echo ========================================

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt pyinstaller==6.3.0

REM Build with PyInstaller
echo Building executable...
pyinstaller build.spec --clean --noconfirm

REM Create release package
echo Creating release package...
if not exist release mkdir release
if not exist release\windows mkdir release\windows

cd dist

REM Create ZIP archive
echo Creating ZIP archive...
powershell -Command "Compress-Archive -Path 'ai_usage_dash\*' -DestinationPath '..\release\windows\ai_usage_dash_windows.zip' -Force"

REM Create installer script
echo Creating installer script...
(
echo @echo off
echo echo ========================================
echo echo Installing AI Usage Dashboard...
echo echo ========================================
echo.
echo mkdir "%%APPDATA%%\AIUsageDash" 2^>nul
echo mkdir "%%APPDATA%%\AIUsageDash\logs" 2^>nul
echo.
echo copy ai_usage_dash.exe "%%APPDATA%%\AIUsageDash\" /y
echo.
echo echo Creating Start Menu shortcut...
echo powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\AI Usage Dashboard.lnk'); $Shortcut.TargetPath = '%%APPDATA%%\AIUsageDash\ai_usage_dash.exe'; $Shortcut.WorkingDirectory = '%%APPDATA%%\AIUsageDash'; $Shortcut.Save()"
echo.
echo echo ========================================
echo echo Installation complete!
echo echo ========================================
echo echo Run 'ai_usage_dash.exe' to start the application
echo echo.
echo pause
) > ..\release\windows\install.bat

cd /d "%SCRIPT_DIR%"

echo ========================================
echo Build complete!
echo Output: release\windows\
echo ========================================

pause
