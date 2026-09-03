@echo off
title DARAZBOT PRO ENTERPRISE - 1-CLICK DESKTOP LAUNCHER
color 0b
cd /d "%~dp0"

echo ===============================================================================
echo            ⚡ DARAZBOT PRO ENTERPRISE - DESKTOP SUITE v2.1 ⚡
echo       Organic SERP Ranking, 250+ Self-Orders & Auto-Pilot Proxy Engine
echo ===============================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] ERROR: Python is not installed or not in your PATH.
    echo [*] Please install Python 3.10+ from python.org and check 'Add to PATH'.
    pause
    exit /b 1
)

:: 2. Check and Install Requirements
echo [*] [1/3] Verifying Python libraries and dependencies...
python -m pip install -r requirements.txt --quiet --no-warn-script-location

:: 3. Check Playwright Chromium Browser
echo [*] [2/3] Checking Chromium browser engine...
python -m playwright install chromium

:: 4. Create Desktop Shortcut if not exists
if not exist "%USERPROFILE%\Desktop\DarazBot Pro.lnk" (
    echo [*] Pinning DarazBot Pro icon to Windows Desktop...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
      "$ws = New-Object -ComObject WScript.Shell; " ^
      "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
      "$shortcut = $ws.CreateShortcut(\"$desktop\DarazBot Pro.lnk\"); " ^
      "$shortcut.TargetPath = '%~dp0Start_DarazBot_Pro.bat'; " ^
      "$shortcut.WorkingDirectory = '%~dp0'; " ^
      "$shortcut.Description = 'DarazBot Pro Enterprise Suite'; " ^
      "$iconPath = '%~dp0frontend\assets\icon.ico'; " ^
      "if (Test-Path $iconPath) { $shortcut.IconLocation = \"$iconPath,0\" }; " ^
      "$shortcut.Save();" >nul 2>&1
)

:: 5. Launch Full Native Desktop Application
echo [*] [3/3] Launching DarazBot Pro Desktop Application...
echo.
python desktop_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Application closed with exit code %ERRORLEVEL%.
    pause
)
