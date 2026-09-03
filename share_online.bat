@echo off
title DarazBot Pro - Free 1-Click Online Cloud Tunnel
echo ========================================================
echo   DarazBot Pro - 1-Click Free Public Online Sharing
echo ========================================================
echo.
echo Checking Cloudflare Tunnel (cloudflared)...

where cloudflared >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Downloading lightweight cloudflared tool for free online link...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
)

echo.
echo [SUCCESS] Starting Free Global HTTPS Tunnel for your Dashboard...
echo [INFO] Share the generated https://*.trycloudflare.com link with your client!
echo.
if exist "cloudflared.exe" (
    .\cloudflared.exe tunnel --url http://127.0.0.1:8765
) else (
    cloudflared tunnel --url http://127.0.0.1:8765
)
pause
