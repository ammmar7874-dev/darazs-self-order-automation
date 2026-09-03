from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Session, select
from backend.database import engine, Proxy
from backend.core.proxy_rotator import ProxyManager, FreeProxyHarvester
import datetime

router = APIRouter(prefix="/api/proxies", tags=["Proxies"])

class ProxyCreate(BaseModel):
    proxy_url: str
    proxy_type: str = "residential"
    rotation_url: Optional[str] = None

class ProxyTestRequest(BaseModel):
    proxy_url: str
    rotation_url: Optional[str] = None

class RotateRequest(BaseModel):
    method: str = "auto" # android_adb, dongle_hilink, cloudflare_warp, api_webhook, auto
    target_param: Optional[str] = None

@router.get("", response_model=List[Proxy])
def list_proxies():
    with Session(engine) as session:
        return session.exec(select(Proxy).order_by(Proxy.id.desc())).all()

@router.post("", response_model=Proxy)
def create_proxy(data: ProxyCreate):
    with Session(engine) as session:
        proxy = Proxy(
            proxy_url=data.proxy_url.strip(),
            proxy_type=data.proxy_type,
            rotation_url=data.rotation_url.strip() if data.rotation_url else None,
            is_active=True
        )
        session.add(proxy)
        session.commit()
        session.refresh(proxy)
        return proxy

@router.post("/harvest-free")
async def harvest_free_proxies(max_valid: int = 15):
    """
    Scrapes thousands of free proxies from verified global GitHub & API feeds,
    concurrently validates them, and inserts the fastest live working proxies into the DB.
    """
    valid_proxies = await FreeProxyHarvester.harvest_and_validate(max_tested=60, max_valid=max_valid)
    added_count = 0
    with Session(engine) as session:
        for p_info in valid_proxies:
            url = p_info["proxy_url"]
            existing = session.exec(select(Proxy).where(Proxy.proxy_url == url)).first()
            if not existing:
                proxy = Proxy(
                    proxy_url=url,
                    proxy_type="free_global",
                    last_ip=p_info.get("ip"),
                    last_tested_at=datetime.datetime.utcnow(),
                    is_active=True
                )
                session.add(proxy)
                added_count += 1
        session.commit()
    
    return {
        "status": "success",
        "found_valid": len(valid_proxies),
        "added_to_database": added_count,
        "proxies": valid_proxies
    }

@router.get("/current-ip")
async def get_system_ip():
    """Fetches outbound IP & full Geo details (City, Country, ISP) without CORS issues."""
    ip_info = await ProxyManager.get_current_ip()
    return ip_info

@router.get("/adb-devices")
def get_adb_devices():
    """Returns attached Android phones for free 4G mobile IP rotation."""
    devs = ProxyManager.check_adb_devices()
    return {"connected_devices": devs, "count": len(devs)}

@router.post("/rotate")
async def trigger_rotation(data: RotateRequest):
    """
    Triggers IP rotation via Android ADB 4G, HiLink Dongle, Cloudflare WARP, or API Webhook.
    """
    res = await ProxyManager.rotate_ip(rotation_method=data.method, target_param=data.target_param)
    return res

@router.post("/test")
async def test_proxy(data: ProxyTestRequest):
    proxy_dict = ProxyManager.parse_proxy(data.proxy_url)
    ip_info = await ProxyManager.get_current_ip(proxy_dict)
    return {
        "success": "Offline" not in ip_info.get("ip", ""),
        "data": ip_info
    }

@router.delete("/{proxy_id}")
def delete_proxy(proxy_id: int):
    with Session(engine) as session:
        p = session.get(Proxy, proxy_id)
        if not p:
            raise HTTPException(status_code=404, detail="Proxy not found")
        session.delete(p)
        session.commit()
        return {"status": "deleted", "proxy_id": proxy_id}
