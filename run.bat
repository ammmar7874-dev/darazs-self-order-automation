@echo off
title DarazBot Pro - Automation Suite
color 0b

echo ================================================================
echo           ⚡ DARAZBOT PRO - AUTOMATION SUITE v2.0 ⚡
echo   Self-Orders, Organic Ranking, Add-To-Cart & Proxy Rotator
echo ================================================================
echo.

cd /d "%~dp0"

echo [*] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet

echo [*] Starting DarazBot Engine Server on http://127.0.0.1:8765 ...
start http://127.0.0.1:8765

python -m backend.main
pause
