import os
import sys
from pathlib import Path
from pydantic import BaseModel

if getattr(sys, 'frozen', False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_ROOT = Path(sys.executable).parent
else:
    BUNDLE_DIR = Path(__file__).resolve().parent.parent
    APP_ROOT = BUNDLE_DIR

BASE_DIR = BUNDLE_DIR

# Reliable Windows User AppData for 100% guaranteed read/write permissions
if sys.platform == "win32":
    DATA_DIR = Path(os.path.expandvars(r"%LOCALAPPDATA%\DarazBotPro"))
else:
    DATA_DIR = APP_ROOT / "data"

PROFILES_DIR = DATA_DIR / "browser_profiles"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DB_PATH = DATA_DIR / "daraz_automation.db"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True, parents=True)
PROFILES_DIR.mkdir(exist_ok=True, parents=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True, parents=True)

# Daraz Regional Marketplaces
DARAZ_MARKETPLACES = {
    "PK": {"name": "Pakistan 🇵🇰", "url": "https://www.daraz.pk", "login_url": "https://member.daraz.pk/user/login"},
    "BD": {"name": "Bangladesh 🇧🇩", "url": "https://www.daraz.com.bd", "login_url": "https://member.daraz.com.bd/user/login"},
    "LK": {"name": "Sri Lanka 🇱🇰", "url": "https://www.daraz.lk", "login_url": "https://member.daraz.lk/user/login"},
    "NP": {"name": "Nepal 🇳🇵", "url": "https://www.daraz.com.np", "login_url": "https://member.daraz.com.np/user/login"},
    "MM": {"name": "Myanmar 🇲🇲", "url": "https://www.shop.com.mm", "login_url": "https://member.shop.com.mm/user/login"},
}

class Settings(BaseModel):
    app_name: str = "DarazBot Pro Automation Suite"
    version: str = "2.1.0"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8765
    db_url: str = f"sqlite:///{DB_PATH.as_posix()}"
    default_headless: bool = False
    default_concurrency: int = 2
    default_max_orders_per_account: int = 5
    default_cooldown_hours: int = 24
    active_country: str = "PK"
    daraz_base_url: str = "https://www.daraz.pk"
    safe_order_mode: bool = True
    enable_live_orders: bool = True
    human_profile: str = "ultra_stealth"

settings = Settings()
