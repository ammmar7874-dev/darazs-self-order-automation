@echo off
title DARAZBOT PRO v2.1 ENTERPRISE - DESKTOP SUITE
cd /d "%~dp0"

echo ===============================================================================
echo            DARAZBOT PRO v2.1 ENTERPRISE - WINDOWS DESKTOP SUITE
echo       Organic SERP Ranking, Store Booster, Self-Order & Live Monitor
echo ===============================================================================
echo.
echo [*] Initializing engine & launching desktop application...
python desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] App exited with error code %ERRORLEVEL%.
    pause
)

