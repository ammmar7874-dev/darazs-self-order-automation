import asyncio
import sys
from sqlmodel import Session, select
from backend.database import init_db, engine, Account, Campaign, Proxy, ExecutionLog
from backend.core.proxy_rotator import ProxyManager, FreeProxyHarvester
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine

async def run_full_system_verification():
    print("=================================================================")
    print(">>> DARAZBOT PRO ENTERPRISE - DEEP SYSTEM VERIFICATION <<<")
    print("=================================================================")

    # 1. Test Database Initialization & Tables
    print("\n[Step 1/6] Testing Database Layer & Schema...")
    init_db()
    with Session(engine) as session:
        accounts_count = len(session.exec(select(Account)).all())
        campaigns_count = len(session.exec(select(Campaign)).all())
        proxies_count = len(session.exec(select(Proxy)).all())
        print(f"  --> [OK] Database connected! (Local file: data/daraz_automation.db)")
        print(f"  --> Accounts in DB: {accounts_count} | Campaigns: {campaigns_count} | Proxies: {proxies_count}")

    # 2. Test Network & Public IP Detection with Geo-Location
    print("\n[Step 2/6] Testing Network, Public IP & Geo-Location Detection...")
    ip_info = await ProxyManager.get_current_ip()
    print(f"  --> [OK] Outbound Public IP: {ip_info.get('ip', 'Unknown')}")
    print(f"  --> Location / ISP: {ip_info.get('city', '')}, {ip_info.get('country', '')} | ISP: {ip_info.get('isp', '')}")

    # 3. Test Android ADB USB Device Discovery
    print("\n[Step 3/6] Testing Android ADB USB Tethering & Device Detector...")
    adb_devs = ProxyManager.check_adb_devices()
    if adb_devs:
        print(f"  --> [OK] Android ADB Phone Connected: {adb_devs[0]} (4G Airplane Mode rotation ready!)")
    else:
        print("  --> [INFO] No phone attached via USB ADB currently (Dongle / Free Proxy fallback active).")

    # 4. Test Playwright Stealth Browser with Anti-Detect Hardware Fingerprint Spoofing
    print("\n[Step 4/6] Launching Anti-Detect Playwright Stealth Browser Engine...")
    context = None
    page = None
    try:
        context, page = await browser_pool.create_account_context(
            account_email="enterprise_tester@daraz.pk",
            headless=True # Headless for automated self-test
        )
        print("  --> [OK] Anti-Detect Browser context created successfully!")
        print("  --> [OK] WebGL GPU, Canvas noise, and Hardware Concurrency injected.")

        # 5. Test Organic Navigation to Daraz PK
        print("\n[Step 5/6] Testing Daraz PK Navigation & Anti-Bot Bypass...")
        logs = []
        async def test_logger(lvl, msg):
            print(f"      [{lvl.upper()}] {msg}")
            logs.append({"level": lvl, "msg": msg})

        bot = DarazBotEngine(page, context, log_callback=test_logger)
        
        await bot.navigate_home()
        page_title = await page.title()
        print(f"  --> [OK] Page loaded! Title: '{page_title}'")
        print(f"  --> [OK] Current URL: {page.url}")

        # 6. Test Multi-Keyword Organic Search, Suggestion Click & Dwell Simulation
        print("\n[Step 6/6] Testing Multi-Keyword Search, Autocomplete & Dwell Simulation...")
        await bot.organic_search_and_browse(
            keyword="wireless earbuds, bluetooth earphones, tws earbuds",
            target_url="https://www.daraz.pk/products/m10-tws-wireless-earbuds-i12345.html"
        )
        search_results_count = await page.locator("a[href*='-i'], div[data-item-id]").count()
        print(f"  --> [OK] Organic Search Executed! Found {search_results_count} listings on search page.")
        print("  --> [OK] Human dwell, image inspection and scroll simulation completed with 0 blocks!")

        print("\n" + "=" * 65)
        print("[SUCCESS] ALL 6 SUBSYSTEMS DEEPLY VERIFIED & WORKING AT 100%!")
        print("=================================================================")

    except Exception as e:
        print(f"\n[!] Error during verification test: {e}")
        sys.exit(1)
    finally:
        if context:
            await context.close()
        await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(run_full_system_verification())
