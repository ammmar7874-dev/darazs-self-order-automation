@echo off
title Auto Git Sync - 5 Minute Auto Backup
color 0a

echo ================================================================
echo           🚀 AUTO GIT SYNC & AUTO PUSH SERVICE
echo   Har 5 minute baad aapka code automatically GitHub par push hoga
echo ================================================================
echo.

cd /d "%~dp0"

:: Sync interval in seconds (60 seconds = 1 minute)
set INTERVAL=60

:loop
echo [%time:~0,8%] Checking for project changes...

:: Check if there are any modified, added, or deleted files
git status --porcelain > "%temp%\git_status_check.txt"

for %%I in ("%temp%\git_status_check.txt") do if %%~zI gtr 0 (
    echo [*] Nayi changes mili hain! Staging and committing...
    
    git add .
    
    :: Get date and time for commit message
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set datetime=%%I
    set formatted_time=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%:%datetime:~12,2%
    
    git commit -m "auto-sync: %formatted_time%"
    
    echo [*] Pushing to GitHub (origin main)...
    git push origin main
    
    if errorlevel 1 (
        echo [!] Push mein error aaya. Internet check karein. Agle cycle mein dubara try hoga.
    ) else (
        echo [✓] Successfully committed and pushed to GitHub at %formatted_time%!
    )
) else (
    echo [i] Koi nayi change nahi hai. Repository clean hai.
)

echo.
echo [*] Agla auto-sync 5 minute (300 seconds) baad hoga. (Press Ctrl+C to stop)
echo ----------------------------------------------------------------
timeout /t %INTERVAL% /nobreak >nul
goto loop
