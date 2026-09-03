@echo off
title BUILD DARAZBOT PRO STANDALONE DESKTOP APP (.EXE)
color 0b
cd /d "%~dp0"

echo ===============================================================================
echo            ⚡ BUILDING STANDALONE CLOSED-SOURCE DESKTOP APP (.EXE) ⚡
echo       Compiles all Python files into binary. Sellers will NOT see any code!
echo ===============================================================================
echo.

python build_exe.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===============================================================================
    echo [DONE] The compiled standalone application is in: dist\DarazBotPro\
    echo You can now send the 'dist\DarazBotPro' folder to sellers!
    echo Inside it, they will only see 'DarazBotPro.exe' with the custom icon.
    echo ===============================================================================
) else (
    echo [!] Build encountered an error.
)

pause
