@echo off
title Stop Auto Git Sync
color 0c

echo ================================================================
echo           🛑 STOPPING AUTO GIT SYNC BACKGROUND SERVICE
echo ================================================================
echo.

powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*auto_sync.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host '[✓] Stopped process ID:' $_.ProcessId }"

echo.
echo [✓] Auto Git Sync service stopped successfully.
echo ================================================================
pause
