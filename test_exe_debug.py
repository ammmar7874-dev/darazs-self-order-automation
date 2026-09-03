import sys
import os
import traceback
import time

log_file = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "startup_debug.log")

def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

log(f"Python sys.executable: {sys.executable}")
log(f"sys.frozen: {getattr(sys, 'frozen', False)}")
log(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not frozen')}")

try:
    log("Importing backend.config...")
    from backend.config import settings, BASE_DIR, DATA_DIR, DB_PATH
    log(f"BASE_DIR: {BASE_DIR}")
    log(f"DATA_DIR: {DATA_DIR}")
    log(f"DB_PATH: {DB_PATH}")
    log(f"Frontend exists at BASE_DIR / 'frontend': {(BASE_DIR / 'frontend').exists()}")
    log(f"Frontend dir contents: {os.listdir(str(BASE_DIR / 'frontend')) if (BASE_DIR / 'frontend').exists() else 'N/A'}")

    log("Importing backend.database...")
    from backend.database import init_db, engine
    init_db()
    log("Database initialized successfully!")

    log("Importing backend.main...")
    from backend.main import app
    log("FastAPI app imported successfully!")

    log("Testing Uvicorn server start...")
    import uvicorn
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8765, log_level="info", loop="asyncio")
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    log("Uvicorn Config created successfully!")

except Exception as e:
    log(f"FATAL ERROR during startup: {e}")
    log(traceback.format_exc())

log("Debug script completed.")
