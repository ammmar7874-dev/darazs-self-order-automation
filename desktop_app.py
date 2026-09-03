import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

import io

# PyInstaller Windowed Mode stdout/stderr safety shim (Prevents isatty AttributeError)
class SafeLogStream:
    def write(self, s):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False
    def fileno(self):
        raise io.UnsupportedOperation

if sys.stdout is None:
    sys.stdout = SafeLogStream()
if sys.stderr is None:
    sys.stderr = SafeLogStream()
if sys.stdin is None:
    sys.stdin = io.StringIO()

# Ensure UTF-8 output encoding on Windows if streams exist
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.config import settings, BASE_DIR, DATA_DIR, SCREENSHOTS_DIR, APP_ROOT

# Enforce working directory so relative paths always resolve properly
try:
    os.chdir(str(APP_ROOT))
except Exception:
    pass

def log_debug(msg: str):
    try:
        log_file = DATA_DIR / "desktop_debug.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

ICON_ICO = BASE_DIR / "frontend" / "assets" / "icon.ico"
ICON_PNG = BASE_DIR / "frontend" / "assets" / "icon.png"

class DesktopBridgeAPI:
    """Native Python API exposed directly to the webview frontend."""
    
    def __init__(self, window=None):
        self.window = window

    def open_data_dir(self):
        """Opens user data folder in Windows File Explorer."""
        try:
            if sys.platform == "win32":
                os.startfile(str(DATA_DIR))
            else:
                subprocess.Popen(["xdg-open", str(DATA_DIR)])
            return {"status": "ok", "path": str(DATA_DIR)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def open_screenshots_dir(self):
        """Opens screenshots folder in Windows File Explorer."""
        try:
            if sys.platform == "win32":
                os.startfile(str(SCREENSHOTS_DIR))
            else:
                subprocess.Popen(["xdg-open", str(SCREENSHOTS_DIR)])
            return {"status": "ok", "path": str(SCREENSHOTS_DIR)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_desktop_shortcut(self):
        """Creates Windows desktop shortcut with icon."""
        try:
            from backend.api.system import create_desktop_shortcut
            return create_desktop_shortcut()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def toggle_fullscreen(self):
        """Toggles fullscreen window state."""
        if self.window:
            self.window.toggle_fullscreen()
            return {"status": "ok"}
        return {"status": "error", "message": "No active window"}

    def minimize(self):
        """Minimizes the desktop app window."""
        if self.window:
            self.window.minimize()
            return {"status": "ok"}
        return {"status": "error", "message": "No active window"}

    def get_system_info(self):
        """Returns desktop host environment details."""
        import platform
        return {
            "app_name": settings.app_name,
            "version": settings.version,
            "os": platform.system(),
            "os_release": platform.release(),
            "python_version": platform.python_version(),
            "port": settings.port,
            "mode": "desktop_native"
        }

def launch_native_app_window(url: str):
    """Lauches high-performance native desktop app window using Microsoft Edge or Chrome."""
    time.sleep(1.2)
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]
    web_profile_dir = DATA_DIR / "web_profile"
    web_profile_dir.mkdir(parents=True, exist_ok=True)

    for p in edge_paths:
        if os.path.exists(p):
            try:
                proc = subprocess.Popen([
                    p,
                    f"--app={url}",
                    "--start-maximized",
                    f"--app-id=DarazBotProEnterprise",
                    f"--user-data-dir={str(web_profile_dir)}"
                ])
                log_debug(f"Native app window launched with PID {proc.pid}")
                return proc
            except Exception as e:
                log_debug(f"Error launching native browser window: {e}")

    # Fallback to default browser
    try:
        webbrowser.open(url)
    except Exception:
        pass
    return None

def main():
    print("=" * 72)
    print(f"[*] Starting {settings.app_name} v{settings.version} [Enterprise Desktop Suite]")
    print(f"[*] Engine Mode: SERP Organic Ranking, 250+ Self-Orders & Auto-Pilot Proxy")
    print("=" * 72)

    app_url = f"http://127.0.0.1:{settings.port}"
    
    # 1. Launch native app window in parallel
    window_thread = threading.Thread(target=launch_native_app_window, args=(app_url,), daemon=True)
    window_thread.start()

    # 2. Run FastAPI Backend directly in Main Thread for 100% reliability & zero deadlock
    import uvicorn
    from backend.main import app
    
    print(f"[*] Automation Engine & WebSockets running at: {app_url}")
    try:
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            log_config=None,
            log_level="warning",
            access_log=False
        )
    except (KeyboardInterrupt, SystemExit):
        print("\n[*] DarazBot Pro exited gracefully.")

if __name__ == "__main__":
    main()
