import sys
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pathlib import Path

from backend.config import settings, BASE_DIR
from backend.database import init_db
from backend.api import accounts, proxies, campaigns, logs, system
from backend.core.task_scheduler import scheduler
from backend.core.browser_pool import browser_pool

# WebSocket Connection Manager for Live Terminal and Event Broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Hook broadcaster to task scheduler
scheduler.set_broadcast(manager.broadcast)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.reset_stuck_campaigns()
    print(f"[*] {settings.app_name} initialized. Server running on http://{settings.host}:{settings.port}")
    yield
    await browser_pool.stop()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Daraz Self-Order, Keyword Search & Add-To-Cart Automation Engine",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive and receive any client ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# Include API Routers
app.include_router(accounts.router)
app.include_router(proxies.router)
app.include_router(campaigns.router)
app.include_router(logs.router)
app.include_router(system.router)

# Mount Frontend Static Files
frontend_dir = BASE_DIR / "frontend"
if not frontend_dir.exists():
    frontend_dir.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.host, port=settings.port, reload=False)
