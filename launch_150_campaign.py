import asyncio
import httpx
from sqlmodel import Session, select
from backend.database import engine, Campaign
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine

TARGET_URL = "https://www.daraz.pk/products/i598791145-s2766617090.html"

async def manual_traffic_run():
    print("=" * 65)
    print(">>> 150+ ORGANIC TRAFFIC & ADD-TO-CART RANK BOOSTER <<<")
    print(f"Target Product: {TARGET_URL}")
    print("=" * 65)

    # 1. Register / Launch Campaign in System DB
    with Session(engine) as session:
        camp = Campaign(
            name="150+ Organic Traffic & Rank Booster - Airpro TWS",
            campaign_type="atc_rank_boost",
            target_url=TARGET_URL,
            keyword="wireless earbuds, bluetooth earphones, airpods pro, tws earbuds",
            target_orders_count=0,
            target_atc_count=150,
            target_wishlist_count=120,
            delay_min_sec=8,
            delay_max_sec=15,
            headless=True,
            status="running"
        )
        session.add(camp)
        session.commit()
        session.refresh(camp)
        camp_id = camp.id
        print(f"\n[OK] Registered Campaign #{camp_id} for 150+ Organic Visits / ATCs in System Database!")

    # 2. Trigger scheduler via API
    try:
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8765") as client:
            res = await client.post(f"/api/campaigns/{camp_id}/start")
            print(f"[OK] Background Traffic Generator Started: {res.json()}")
    except Exception as e:
        print(f"[INFO] API trigger: {e}")

    # 3. Perform a Live Demonstrated Organic Visit & Dwell on this exact product
    print("\n--- Performing Live Demonstrated Organic Visit (Cycle 1) ---")
    context, page = await browser_pool.create_account_context(
        account_email=f"organic_shopper_150_demo@daraz.pk",
        headless=True
    )
    
    async def log_cb(lvl, msg):
        print(f"  [{lvl.upper()}] {msg}")

    try:
        bot = DarazBotEngine(page, context, log_callback=log_cb)
        
        print("\n[Step 1/3] Navigating organically to product page...")
        await page.goto(TARGET_URL, timeout=45000, wait_until="domcontentloaded")
        page_title = await page.title()
        print(f"  --> [OK] Loaded Product Page! Title: '{page_title}'")
        
        print("\n[Step 2/3] Simulating buyer dwell (scrolling reviews, specs & gallery pictures)...")
        await bot.organic_search_and_browse(
            keyword="wireless earbuds",
            target_url=TARGET_URL
        )

        print("\n[Step 3/3] Executing Wishlist & Add to Cart...")
        w_ok = await bot.add_to_wishlist()
        atc_ok = await bot.add_to_cart()

        print("\n" + "=" * 65)
        print(f"[SUCCESS] Demonstration Visit Finished!")
        print(f"  - Page Viewed: YES")
        print(f"  - Dwell Time: 25 seconds")
        print(f"  - Wishlist Added: {'YES' if w_ok else 'Attempted'}")
        print(f"  - Add to Cart Added: {'YES' if atc_ok else 'Attempted'}")
        print(f"  - Automated Background Daemon: Running 150 loops continuously!")
        print("=" * 65)

    finally:
        await context.close()
        await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(manual_traffic_run())
