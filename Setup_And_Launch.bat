@echo off
title DARAZBOT PRO - 1-CLICK SELLER APP LAUNCHER
color 0b
cd /d "%~dp0"

echo ===============================================================================
echo            ⚡ DARAZBOT PRO ENTERPRISE - SELLER DESKTOP APP ⚡
echo       Organic SERP Ranking, 250+ Self-Orders & Auto-Pilot Proxy Suite
echo ===============================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not installed on this PC.
    echo [*] Opening official Python download page in 3 seconds...
    echo [*] IMPORTANT: When installing Python, CHECK the box 'Add Python to PATH'!
    timeout /t 3 >nul
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Check and install dependencies (fast & quiet)
echo [*] [1/3] Setting up environment and libraries (First time may take 1-2 minutes)...
python -m pip install -r requirements.txt --quiet --no-warn-script-location

:: 3. Check Playwright Chromium Browser Engine
echo [*] [2/3] Verifying Chromium automation engine...
python -m playwright install chromium

:: 4. Create Desktop Shortcut icon on Windows Desktop
echo [*] [3/3] Creating 1-Click Desktop App Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
  "$shortcut = $ws.CreateShortcut(\"$desktop\DarazBot Pro.lnk\"); " ^
  "$shortcut.TargetPath = '%~dp0Setup_And_Launch.bat'; " ^
  "$shortcut.WorkingDirectory = '%~dp0'; " ^
  "$shortcut.Description = 'DarazBot Pro Enterprise Desktop App'; " ^
  "$iconPath = '%~dp0frontend\assets\icon.ico'; " ^
  "if (Test-Path $iconPath) { $shortcut.IconLocation = \"$iconPath,0\" }; " ^
  "$shortcut.Save();" >nul 2>&1

echo.
echo ===============================================================================
echo [SUCCESS] DarazBot Pro is ready! Launching Desktop App Window...
echo ===============================================================================
echo.

:: 5. Launch Native Desktop App
python desktop_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] App closed with code %ERRORLEVEL%.
    pause
)
