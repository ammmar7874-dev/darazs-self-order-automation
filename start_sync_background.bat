@echo off
title Start Auto Git Sync (Background)
color 0a

echo ================================================================
echo           🚀 STARTING AUTO GIT SYNC (BACKGROUND)
echo ================================================================
echo.

cd /d "%~dp0"

echo [*] Starting silent background sync process...
powershell -Command "Start-Process powershell -ArgumentList '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""%~dp0auto_sync.ps1""' -WindowStyle Hidden"

echo.
echo [✓] Auto Git Sync is now RUNNING in the background!
echo [i] Har 1 minute (60 seconds) baad aapka code automatically GitHub par push hoga.
echo [i] Sync logs dekhne ke liye 'auto_sync.log' check kar sakte hain.
echo.
echo Agar aap isay stop karna chahein toh 'stop_sync_background.bat' run karein.
echo ================================================================
echo.
pause
