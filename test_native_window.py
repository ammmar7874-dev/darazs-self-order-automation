import os
import sys
import time
import subprocess
import threading
import uvicorn
from backend.main import app
from backend.config import settings

def launch_window():
    time.sleep(1.5)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for p in edge_paths:
        if os.path.exists(p):
            print(f"[*] Found native engine: {p}")
            proc = subprocess.Popen([
                p,
                f"--app=http://127.0.0.1:{settings.port}",
                "--start-maximized",
                f"--app-id=DarazBotProEnterprise",
                f"--user-data-dir={os.path.expandvars(r'%LOCALAPPDATA%\DarazBotPro\web_profile')}"
            ])
            print("[*] Native App Window launched with PID:", proc.pid)
            return proc
    return None

if __name__ == "__main__":
    t = threading.Thread(target=launch_window, daemon=True)
    t.start()
    print("[*] Starting Main FastAPI Uvicorn Server on port", settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info", access_log=False)
