import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.config import settings, BASE_DIR, DATA_DIR, SCREENSHOTS_DIR

router = APIRouter(prefix="/api/system", tags=["System & Desktop"])

class FolderRequest(BaseModel):
    target: str # "data", "screenshots", "root", "logs"

class ShortcutRequest(BaseModel):
    desktop: bool = True

@router.get("/info")
@router.get("/status")
def get_system_info():
    """Returns desktop host environment details, disk space, and runtime diagnostics."""
    db_file = DATA_DIR / "daraz_automation.db"
    db_size_kb = round(db_file.stat().st_size / 1024, 2) if db_file.exists() else 0

    # Count screenshots
    ss_count = len(list(SCREENSHOTS_DIR.glob("*.png"))) if SCREENSHOTS_DIR.exists() else 0

    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "os": platform.system(),
        "os_release": platform.release(),
        "python_version": platform.python_version(),
        "port": settings.port,
        "data_dir": str(DATA_DIR),
        "screenshots_dir": str(SCREENSHOTS_DIR),
        "screenshots_count": ss_count,
        "db_size_kb": db_size_kb,
        "status": "healthy",
        "live_mode": settings.enable_live_orders
    }

@router.post("/open-folder")
def open_folder(req: FolderRequest):
    """Opens designated folder in Windows Explorer."""
    target = req.target.lower()
    path = BASE_DIR
    if target == "data":
        path = DATA_DIR
    elif target == "screenshots":
        path = SCREENSHOTS_DIR
    elif target == "root":
        path = BASE_DIR

    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return {"status": "ok", "opened": str(path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-desktop-shortcut")
def create_desktop_shortcut():
    """Creates a direct Windows Desktop shortcut for DarazBot Pro with custom icon."""
    if sys.platform != "win32":
        return {"status": "skipped", "message": "Only available on Windows"}

    try:
        desktop_dir = Path(os.path.expandvars(r"%USERPROFILE%\Desktop"))
        shortcut_path = desktop_dir / "DarazBot Pro.lnk"
        bat_path = BASE_DIR / "DarazBot_Pro_Desktop.bat"
        icon_path = BASE_DIR / "frontend" / "assets" / "icon.ico"

        vbs_script = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{bat_path}"
oLink.WorkingDirectory = "{BASE_DIR}"
oLink.Description = "DarazBot Pro Enterprise - Desktop Suite"
If oWS.CreateObject("Scripting.FileSystemObject").FileExists("{icon_path}") Then
    oLink.IconLocation = "{icon_path}, 0"
End If
oLink.Save
"""
        temp_vbs = BASE_DIR / "_create_shortcut.vbs"
        with open(temp_vbs, "w", encoding="utf-8") as f:
            f.write(vbs_script)

        subprocess.run(["cscript", "//Nologo", str(temp_vbs)], check=True)
        if temp_vbs.exists():
            temp_vbs.unlink()

        return {"status": "ok", "shortcut": str(shortcut_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create shortcut: {e}")
