import os
import sys
import shutil
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("=================================================================")
    print("[*] BUILDING DARAZBOT PRO - STANDALONE DESKTOP EXECUTABLE (.EXE)")
    print("=================================================================")
    
    icon_path = BASE_DIR / "frontend" / "assets" / "icon.ico"
    frontend_path = BASE_DIR / "frontend"
    backend_path = BASE_DIR / "backend"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--name=DarazBotPro",
        f"--icon={icon_path}",
        f"--add-data={frontend_path};frontend",
        f"--add-data={backend_path};backend",
        "--collect-all=playwright",
        "--collect-all=playwright_stealth",
        "--collect-all=fake_useragent",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespans.on",
        "--hidden-import=fastapi",
        "--hidden-import=sqlmodel",
        "--hidden-import=httpx",
        "--hidden-import=websockets",
        "--hidden-import=sqlite3",
        "--hidden-import=backend.main",
        "--hidden-import=backend.config",
        "--hidden-import=backend.database",
        "--hidden-import=backend.api.accounts",
        "--hidden-import=backend.api.campaigns",
        "--hidden-import=backend.api.proxies",
        "--hidden-import=backend.api.logs",
        "--hidden-import=backend.api.system",
        "--hidden-import=backend.core.daraz_bot",
        "--hidden-import=backend.core.browser_pool",
        "--hidden-import=backend.core.human_behavior",
        "--hidden-import=backend.core.proxy_rotator",
        "--hidden-import=backend.core.task_scheduler",
        str(BASE_DIR / "desktop_app.py")
    ]
    
    print("\n[*] Running PyInstaller compilation...")
    res = subprocess.run(cmd, cwd=str(BASE_DIR))
    if res.returncode == 0:
        print("\n=================================================================")
        print("✔ [BUILD SUCCESSFUL] Standalone App created in: dist/DarazBotPro/")
        print("✔ Protected binary: dist/DarazBotPro/DarazBotPro.exe")
        print("✔ Seller will NEVER see any Python source code!")
        print("=================================================================")
    else:
        print(f"\n[!] Compilation failed with return code {res.returncode}")

if __name__ == "__main__":
    build()
