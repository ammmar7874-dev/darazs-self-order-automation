@echo off
title DARAZBOT PRO - CREATE DESKTOP SHORTCUT
cd /d "%~dp0"

echo ===============================================================================
echo            DARAZBOT PRO - DESKTOP SHORTCUT CREATOR
echo ===============================================================================
echo.
echo [*] Generating high-resolution Windows Desktop shortcut...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; " ^
  "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
  "$shortcut = $ws.CreateShortcut(\"$desktop\DarazBot Pro.lnk\"); " ^
  "$shortcut.TargetPath = '%~dp0DarazBot_Pro_Desktop.bat'; " ^
  "$shortcut.WorkingDirectory = '%~dp0'; " ^
  "$shortcut.Description = 'DarazBot Pro Enterprise Suite'; " ^
  "$iconPath = '%~dp0frontend\assets\icon.ico'; " ^
  "if (Test-Path $iconPath) { $shortcut.IconLocation = \"$iconPath,0\" }; " ^
  "$shortcut.Save(); " ^
  "Write-Host '[+] Successfully created Desktop shortcut: DarazBot Pro on Windows Desktop!' -ForegroundColor Green"

echo.
echo ===============================================================================
echo [SUCCESS] You can now double-click 'DarazBot Pro' directly on your Desktop!
echo ===============================================================================
pause
