import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist" / "DarazBotPro"
OUTPUT_INSTALLER_DIR = BASE_DIR / "installer_build"
SETUP_EXE_OUT = BASE_DIR / "DarazBot_Pro_Enterprise_Setup.exe"

def build_installer():
    print("=" * 72)
    print("[*] BUILDING SINGLE 1-CLICK COMMERCIAL INSTALLER (.EXE)")
    print("=" * 72)

    if not DIST_DIR.exists():
        print("[!] Error: dist/DarazBotPro does not exist. Please run build_exe.py first.")
        return

    OUTPUT_INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUTPUT_INSTALLER_DIR / "app_payload.zip"

    print("[1] Compressing complete application bundle...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(DIST_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, DIST_DIR)
                zf.write(abs_path, rel_path)

    print(f"    ✔ Payload archive created ({zip_path.stat().st_size // 1024 // 1024} MB)")

    # 2. Create the standalone installer stub script
    installer_stub_code = '''# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path

def install():
    try:
        # Determine bundle paths
        if getattr(sys, 'frozen', False):
            bundle_dir = Path(sys._MEIPASS)
        else:
            bundle_dir = Path(__file__).resolve().parent

        target_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\\Programs\\DarazBotPro"))
        target_dir.mkdir(parents=True, exist_ok=True)

        zip_payload = bundle_dir / "app_payload.zip"
        if zip_payload.exists():
            with zipfile.ZipFile(str(zip_payload), 'r') as zf:
                zf.extractall(str(target_dir))

        exe_path = target_dir / "DarazBotPro.exe"

        # Create Desktop Shortcut via PowerShell WScript.Shell
        try:
            ps_cmd = f"""
            $ws = New-Object -ComObject WScript.Shell;
            $desktop = [System.Environment]::GetFolderPath('Desktop');
            $shortcut = $ws.CreateShortcut("$desktop\\DarazBot Pro.lnk");
            $shortcut.TargetPath = '{str(exe_path)}';
            $shortcut.WorkingDirectory = '{str(target_dir)}';
            $shortcut.Description = 'DarazBot Pro Enterprise Automation Suite';
            $shortcut.IconLocation = '{str(exe_path)},0';
            $shortcut.Save();
            """
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], creationflags=0x08000000)
        except Exception:
            pass

        # Launch the application immediately
        if exe_path.exists():
            subprocess.Popen([str(exe_path)], cwd=str(target_dir))
    except Exception:
        pass
    finally:
        sys.exit(0)

if __name__ == "__main__":
    install()
'''

    stub_path = OUTPUT_INSTALLER_DIR / "installer_stub.py"
    with open(stub_path, "w", encoding="utf-8") as f:
        f.write(installer_stub_code)

    print("[2] Compiling standalone setup executable (DarazBot_Pro_Setup.exe)...")
    icon_path = BASE_DIR / "frontend" / "assets" / "icon.ico"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name=DarazBot_Pro_Enterprise_Setup",
        f"--icon={icon_path}",
        f"--add-data={zip_path};.",
        str(stub_path)
    ]

    res = subprocess.run(cmd, cwd=str(OUTPUT_INSTALLER_DIR))
    if res.returncode == 0:
        built_setup = OUTPUT_INSTALLER_DIR / "dist" / "DarazBot_Pro_Enterprise_Setup.exe"
        if built_setup.exists():
            shutil.copy2(str(built_setup), str(BASE_DIR / "DarazBot_Pro_Enterprise_Setup.exe"))
            print("=" * 72)
            print("✔ [SUCCESS] Single 1-Click Installer Created:")
            print(f"👉 {BASE_DIR / 'DarazBot_Pro_Enterprise_Setup.exe'}")
            print("=" * 72)
            print("Seller sirf is 1 file par double-click karega, aur:")
            print("1. Khud install ho jayegi.")
            print("2. Desktop par DarazBot Pro ka icon ban jayega.")
            print("3. App foran khul jayegi!")
            print("=" * 72)
    else:
        print(f"[!] Compilation error: {res.returncode}")

if __name__ == "__main__":
    build_installer()
