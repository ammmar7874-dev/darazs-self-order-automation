@echo off
title BUILD 1-CLICK COMMERCIAL INSTALLER
cd /d "%~dp0"
echo =================================================================
echo [*] GENERATING 1-CLICK STANDALONE INSTALLER SETUP FOR CLIENTS
echo =================================================================
python build_single_installer.py
echo.
pause
