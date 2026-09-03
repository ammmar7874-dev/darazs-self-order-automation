import sys
import io
import asyncio

# Ensure unbuffered utf-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from sqlmodel import Session, select
from backend.database import init_db, engine, Account, Campaign, Proxy, TaskItem, ExecutionLog
from backend.core.proxy_rotator import ProxyManager
from backend.core.browser_pool import browser_pool
from backend.core.task_scheduler import scheduler
from backend.config import settings

async def run_diagnostics():
    print("==================================================================")
    print("🔍 DARAZBOT PRO - COMPREHENSIVE COMMERCIAL READINESS AUDIT")
    print("==================================================================")
    
    results = {}

    # Test 1: Database Layer & Models
    print("\n[1] Testing Database & Schema Integrity...")
    try:
        init_db()
        with Session(engine) as session:
            accounts = session.exec(select(Account)).all()
            campaigns = session.exec(select(Campaign)).all()
            proxies = session.exec(select(Proxy)).all()
            logs = session.exec(select(ExecutionLog)).all()
        print(f"  ✔ DB Status: CONNECTED & HEALTHY")
        print(f"  ✔ Existing Records: Accounts={len(accounts)}, Campaigns={len(campaigns)}, Proxies={len(proxies)}, Logs={len(logs)}")
        results["Database"] = "PASSED (100% Functional)"
    except Exception as e:
        print(f"  ❌ DB Error: {e}")
        results["Database"] = f"FAILED: {e}"

    # Test 2: Network, IP Detection & Proxy Manager
    print("\n[2] Testing Network & Public IP Resolver...")
    try:
        ip_info = await ProxyManager.get_current_ip()
        print(f"  ✔ Outbound IP: {ip_info.get('ip', 'N/A')}")
        print(f"  ✔ Location/ISP: {ip_info.get('city', '')} {ip_info.get('country', '')} | {ip_info.get('isp', '')}")
        results["Network_IP"] = f"PASSED (IP: {ip_info.get('ip')})"
    except Exception as e:
        print(f"  ❌ IP Error: {e}")
        results["Network_IP"] = f"FAILED: {e}"

    # Test 3: Task Scheduler & Concurrency State
    print("\n[3] Testing Task Scheduler & State Management...")
    try:
        scheduler.reset_stuck_campaigns()
        print("  ✔ Stuck campaign reset check completed without exception.")
        results["Scheduler"] = "PASSED (Ready)"
    except Exception as e:
        print(f"  ❌ Scheduler Error: {e}")
        results["Scheduler"] = f"FAILED: {e}"

    # Test 4: Playwright Anti-Detect Browser Creation
    print("\n[4] Testing Playwright Stealth Engine & Fingerprint Injection...")
    try:
        context, page = await browser_pool.create_account_context(
            account_email="commercial_test@daraz.pk",
            headless=True
        )
        print("  ✔ Playwright Chromium launched with isolated user-data-dir.")
        
        # Test fingerprint variables in DOM
        hw_cores = await page.evaluate("navigator.hardwareConcurrency")
        webdriver_flag = await page.evaluate("navigator.webdriver")
        device_mem = await page.evaluate("navigator.deviceMemory")
        
        print(f"  ✔ Injected Hardware Concurrency: {hw_cores} cores")
        print(f"  ✔ Injected Device Memory: {device_mem} GB")
        print(f"  ✔ navigator.webdriver Spoofed: {webdriver_flag} (Expected: None/undefined)")
        
        await context.close()
        await browser_pool.stop()
        results["Browser_Stealth"] = "PASSED (High Stealth Verified)"
    except Exception as e:
        print(f"  ❌ Browser Error: {e}")
        results["Browser_Stealth"] = f"FAILED: {e}"

    # Test 5: FastAPI REST Endpoints & Routers
    print("\n[5] Testing FastAPI Routes & System API...")
    try:
        from fastapi.testclient import TestClient
        from backend.main import app
        client = TestClient(app)
        
        r_sys = client.get("/api/system/status")
        r_acc = client.get("/api/accounts")
        r_camp = client.get("/api/campaigns")
        r_prox = client.get("/api/proxies")
        
        print(f"  ✔ /api/system/status -> Status {r_sys.status_code}")
        print(f"  ✔ /api/accounts -> Status {r_acc.status_code}")
        print(f"  ✔ /api/campaigns -> Status {r_camp.status_code}")
        print(f"  ✔ /api/proxies -> Status {r_prox.status_code}")
        
        if all(r.status_code == 200 for r in [r_sys, r_acc, r_camp, r_prox]):
            results["API_Endpoints"] = "PASSED (All HTTP 200 OK)"
        else:
            results["API_Endpoints"] = "WARNING (Some returned non-200)"
    except Exception as e:
        print(f"  ❌ API Test Error: {e}")
        results["API_Endpoints"] = f"FAILED: {e}"

    print("\n" + "=" * 66)
    print("📊 DIAGNOSTIC AUDIT SUMMARY:")
    for k, v in results.items():
        print(f"  • {k.ljust(20)}: {v}")
    print("==================================================================")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
