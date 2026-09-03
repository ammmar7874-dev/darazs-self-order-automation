from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlmodel import Session, select, func
from pathlib import Path
import os
import base64

from backend.database import engine, ExecutionLog, Account, Campaign, Proxy, RankCheckHistory
from backend.config import settings, SCREENSHOTS_DIR, DARAZ_MARKETPLACES
import datetime

router = APIRouter(prefix="/api/logs", tags=["Logs & Stats"])

@router.get("", response_model=List[ExecutionLog])
def get_logs(limit: int = 150):
    with Session(engine) as session:
        return session.exec(select(ExecutionLog).order_by(ExecutionLog.id.desc()).limit(limit)).all()

@router.delete("")
def clear_logs():
    with Session(engine) as session:
        logs = session.exec(select(ExecutionLog)).all()
        for l in logs:
            session.delete(l)
        session.commit()
        return {"status": "cleared"}

@router.get("/stats")
def get_dashboard_stats():
    with Session(engine) as session:
        total_accounts = session.exec(select(func.count(Account.id))).one()
        active_accounts = session.exec(select(func.count(Account.id)).where(Account.status == "active")).one()
        cooldown_accounts = session.exec(select(func.count(Account.id)).where(Account.status == "cooldown")).one()
        
        total_campaigns = session.exec(select(func.count(Campaign.id))).one()
        running_campaigns = session.exec(select(func.count(Campaign.id)).where(Campaign.status == "running")).one()
        
        campaigns = session.exec(select(Campaign)).all()
        total_orders_placed = sum(c.completed_orders_count for c in campaigns)
        total_atc_done = sum(c.completed_atc_count for c in campaigns)
        total_wishlist_done = sum(c.completed_wishlist_count for c in campaigns)
        
        active_proxies = session.exec(select(func.count(Proxy.id)).where(Proxy.is_active == True)).one()
        total_rank_checks = session.exec(select(func.count(RankCheckHistory.id))).one()

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "cooldown_accounts": cooldown_accounts,
            "total_campaigns": total_campaigns,
            "running_campaigns": running_campaigns,
            "total_orders_placed": total_orders_placed,
            "total_atc_done": total_atc_done,
            "total_wishlist_done": total_wishlist_done,
            "active_proxies": active_proxies,
            "total_rank_checks": total_rank_checks,
            "active_country": settings.active_country,
            "safe_order_mode": settings.safe_order_mode,
            "human_profile": settings.human_profile,
            "daraz_base_url": settings.daraz_base_url,
        }

@router.get("/live-screenshot")
def get_live_screenshot():
    """Returns the latest screenshot captured by active bot worker."""
    latest_img = SCREENSHOTS_DIR / "live_stream.png"
    if not latest_img.exists():
        # Fallback to any recent png
        pngs = list(SCREENSHOTS_DIR.glob("*.png"))
        if pngs:
            pngs.sort(key=os.path.getmtime, reverse=True)
            latest_img = pngs[0]
            
    if latest_img.exists():
        return FileResponse(str(latest_img), media_type="image/png")
    
    # Return 1x1 transparent PNG or 204 if no screenshot yet
    return Response(content=b"", status_code=204)

class SettingsUpdate(BaseModel):
    active_country: Optional[str] = None
    safe_order_mode: Optional[bool] = None
    human_profile: Optional[str] = None
    default_headless: Optional[bool] = None

@router.get("/settings")
def get_settings():
    return {
        "active_country": settings.active_country,
        "daraz_base_url": settings.daraz_base_url,
        "safe_order_mode": settings.safe_order_mode,
        "human_profile": settings.human_profile,
        "default_headless": settings.default_headless,
        "available_marketplaces": DARAZ_MARKETPLACES
    }

@router.post("/settings")
def update_settings(data: SettingsUpdate):
    if data.active_country and data.active_country in DARAZ_MARKETPLACES:
        settings.active_country = data.active_country
        settings.daraz_base_url = DARAZ_MARKETPLACES[data.active_country]["url"]
    if data.safe_order_mode is not None:
        settings.safe_order_mode = data.safe_order_mode
    if data.human_profile:
        settings.human_profile = data.human_profile
    if data.default_headless is not None:
        settings.default_headless = data.default_headless
    return {"status": "success", "settings": get_settings()}

