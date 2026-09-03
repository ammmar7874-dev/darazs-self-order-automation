from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import Session, select
from backend.database import engine, Account
import io
import csv

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])

class AccountCreate(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    full_name: Optional[str] = "Customer"
    shipping_address: Optional[str] = None
    city: Optional[str] = "Karachi"
    max_daily_orders: int = 2

class BulkAccountItem(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None

@router.get("", response_model=List[Account])
def list_accounts():
    with Session(engine) as session:
        return session.exec(select(Account).order_by(Account.id.desc())).all()

@router.post("", response_model=Account)
def create_account(data: AccountCreate):
    with Session(engine) as session:
        existing = session.exec(select(Account).where(Account.email == data.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Account with this email already exists.")
        
        acc = Account(
            email=data.email.strip(),
            password=data.password.strip(),
            phone=data.phone,
            full_name=data.full_name,
            shipping_address=data.shipping_address,
            city=data.city,
            max_daily_orders=data.max_daily_orders,
            status="active"
        )
        session.add(acc)
        session.commit()
        session.refresh(acc)
        return acc

class BulkImportRequest(BaseModel):
    text_data: str

@router.post("/bulk-text")
def bulk_import_text(payload: BulkImportRequest):
    """
    Imports accounts formatted as:
    - email:password
    - email:password:phone:address
    - email | password | phone | address
    - email,password
    """
    lines = payload.text_data.strip().split("\n")
    imported_count = 0
    updated_count = 0
    with Session(engine) as session:
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            # Determine separator (: or | or , or tab)
            parts = []
            if "|" in line_str:
                parts = [p.strip() for p in line_str.split("|")]
            elif "\t" in line_str:
                parts = [p.strip() for p in line_str.split("\t")]
            elif ":" in line_str:
                parts = [p.strip() for p in line_str.split(":")]
            elif "," in line_str:
                parts = [p.strip() for p in line_str.split(",")]

            if len(parts) >= 2:
                email = parts[0].strip()
                password = parts[1].strip()
                phone = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
                address = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
                
                existing = session.exec(select(Account).where(Account.email == email)).first()
                if not existing:
                    acc = Account(
                        email=email,
                        password=password,
                        phone=phone,
                        shipping_address=address,
                        status="active"
                    )
                    session.add(acc)
                    imported_count += 1
                else:
                    # Update existing account credentials & info
                    existing.password = password
                    if phone:
                        existing.phone = phone
                    if address:
                        existing.shipping_address = address
                    existing.status = "active"
                    session.add(existing)
                    updated_count += 1
                    
        session.commit()
    return {"status": "success", "imported": imported_count, "updated": updated_count}


class GlobalLimitRequest(BaseModel):
    max_daily_orders: int = 5

@router.post("/set-global-limit")
def set_global_daily_limit(payload: GlobalLimitRequest):
    """Sets max daily orders limit across all accounts in 1-click."""
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        for acc in accounts:
            acc.max_daily_orders = max(1, payload.max_daily_orders)
            if acc.daily_orders_count < acc.max_daily_orders and acc.status == "cooldown":
                acc.status = "active"
            session.add(acc)
        session.commit()
        return {"status": "success", "updated_count": len(accounts), "new_max_daily_orders": payload.max_daily_orders}

@router.post("/reset-all-quotas")
def reset_all_quotas():
    """Resets daily orders count back to 0 for all accounts in pool."""
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        for acc in accounts:
            acc.daily_orders_count = 0
            if acc.status == "cooldown":
                acc.status = "active"
            session.add(acc)
        session.commit()
        return {"status": "success", "reset_count": len(accounts)}

@router.post("/{account_id}/reset-quota")
def reset_quota(account_id: int):
    with Session(engine) as session:
        acc = session.get(Account, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        acc.daily_orders_count = 0
        acc.status = "active"
        session.add(acc)
        session.commit()
        return {"status": "reset", "account_id": account_id}

@router.post("/{account_id}/open-browser")
async def open_account_browser(account_id: int):
    """
    Opens an interactive visible Chrome window for this account.
    Once user logs in or solves captcha, session cookies are saved to DB forever!
    """
    import json
    import asyncio
    with Session(engine) as session:
        acc = session.get(Account, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        email = acc.email
        phone = acc.phone
        password = acc.password

    async def _launch():
        try:
            from backend.core.browser_pool import browser_pool
            from backend.core.daraz_bot import DarazBotEngine
            context, page = await browser_pool.create_account_context(account_email=email, headless=False)
            bot = DarazBotEngine(page, context)
            
            # Navigate to login page
            await page.goto("https://member.daraz.pk/user/login")
            await asyncio.sleep(2)
            await bot.check_and_login(email, password, phone)
            
            # Poll for 60 seconds to detect successful login & save cookies
            for _ in range(30):
                await asyncio.sleep(2)
                cookies = await context.cookies()
                has_user = any("user" in c.get("name", "").lower() or "token" in c.get("name", "").lower() for c in cookies)
                if has_user:
                    with Session(engine) as session:
                        db_acc = session.get(Account, account_id)
                        if db_acc:
                            db_acc.session_status = "valid"
                            db_acc.cookies_json = json.dumps(cookies)
                            db_acc.status = "active"
                            session.add(db_acc)
                            session.commit()
                    break

            await asyncio.sleep(45)
            try:
                # Save cookies once more before close
                cookies = await context.cookies()
                if cookies:
                    with Session(engine) as session:
                        db_acc = session.get(Account, account_id)
                        if db_acc:
                            db_acc.cookies_json = json.dumps(cookies)
                            session.add(db_acc)
                            session.commit()
                await context.close()
            except Exception:
                pass
        except Exception as e:
            print(f"[OpenBrowser] Error: {e}")

    asyncio.create_task(_launch())
    return {"status": "browser_launched", "account_email": email}



@router.get("/export-csv")
def export_accounts_csv():
    """Exports all accounts into CSV format for easy backup or external use."""
    from fastapi.responses import Response
    with Session(engine) as session:
        accounts = session.exec(select(Account).order_by(Account.id.asc())).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Email", "Password", "Phone", "Status", "Daily Orders", "Total Orders", "Shipping Address", "City", "Created At"])
        for a in accounts:
            writer.writerow([
                a.id, a.email, a.password, a.phone or "", a.status,
                a.daily_orders_count, a.total_orders_placed,
                a.shipping_address or "", a.city or "",
                a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=daraz_accounts_export.csv"}
        )

@router.post("/{account_id}/check-session")
async def check_account_session(account_id: int):
    """Checks if the account browser profile has an active, authenticated Daraz session."""
    from backend.core.browser_pool import browser_pool
    from backend.core.daraz_bot import DarazBotEngine
    with Session(engine) as session:
        acc = session.get(Account, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        email = acc.email
        password = acc.password
        phone = acc.phone

    context = None
    try:
        context, page = await browser_pool.create_account_context(account_email=email, headless=True)
        bot = DarazBotEngine(page, context)
        is_logged = await bot.check_and_login(email, password, phone)
        with Session(engine) as session:
            db_acc = session.get(Account, account_id)
            if db_acc:
                db_acc.status = "active" if is_logged else "needs_otp"
                session.add(db_acc)
                session.commit()
        return {"status": "success", "is_logged_in": is_logged, "account_status": "active" if is_logged else "needs_otp"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if context:
            await context.close()

class OtpRequest(BaseModel):
    service_provider: str = "5sim" # "5sim" or "sms-activate"
    api_key: str
    action: str = "buy" # "buy" or "get_code"
    order_id: Optional[str] = None
    country: str = "pakistan"

@router.post("/otp/virtual-sms")
async def virtual_sms_otp_helper(data: OtpRequest):
    """
    Helps sellers acquire cheap temporary Pakistan/Daraz virtual numbers & OTPs.
    Supports 5SIM (5sim.net) and SMS-Activate.
    """
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if data.service_provider == "5sim":
                headers = {"Authorization": f"Bearer {data.api_key.strip()}", "Accept": "application/json"}
                if data.action == "buy":
                    res = await client.get(f"https://5sim.net/v1/user/buy/activation/{data.country}/any/daraz", headers=headers)
                    if res.status_code == 200:
                        order_data = res.json()
                        return {"success": True, "phone": order_data.get("phone"), "order_id": order_data.get("id"), "status": "PENDING"}
                    return {"success": False, "error": res.text}
                elif data.action == "get_code" and data.order_id:
                    res = await client.get(f"https://5sim.net/v1/user/check/{data.order_id}", headers=headers)
                    if res.status_code == 200:
                        chk = res.json()
                        sms_list = chk.get("sms", [])
                        code = sms_list[0].get("code") if sms_list else None
                        return {"success": True, "code": code, "status": chk.get("status")}
                    return {"success": False, "error": res.text}

            elif data.service_provider == "sms-activate":
                if data.action == "buy":
                    url = f"https://api.sms-activate.org/stubs/handler_api.php?api_key={data.api_key.strip()}&action=getNumber&service=daraz&country=60"
                    res = await client.get(url)
                    if "ACCESS_NUMBER" in res.text:
                        parts = res.text.split(":")
                        return {"success": True, "order_id": parts[1], "phone": parts[2], "status": "PENDING"}
                    return {"success": False, "error": res.text}
                elif data.action == "get_code" and data.order_id:
                    url = f"https://api.sms-activate.org/stubs/handler_api.php?api_key={data.api_key.strip()}&action=getStatus&id={data.order_id}"
                    res = await client.get(url)
                    if "STATUS_OK" in res.text:
                        code = res.text.split(":")[1]
                        return {"success": True, "code": code, "status": "RECEIVED"}
                    return {"success": True, "code": None, "status": res.text}

        return {"success": False, "error": "Unknown service provider or action"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.delete("/{account_id}")
def delete_account(account_id: int):
    with Session(engine) as session:
        acc = session.get(Account, account_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")
        session.delete(acc)
        session.commit()
        return {"status": "deleted", "account_id": account_id}
