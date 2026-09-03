import asyncio
import datetime
import random
import sys
from sqlmodel import Session, select
from backend.database import engine, Campaign, ExecutionLog
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine

PRODUCTS = [
    {
        "id": "667064561",
        "url": "https://www.daraz.pk/products/i667064561.html",
        "title": "Orginal TwS Airpods with Super Sound & High Quality Touch Sensor True Stereo Headphones",
        "name": "Rank Booster: Original TWS Airpods (667064561)",
        "keywords": "wireless earbuds, tws earbuds, bluetooth earphones, airpods, tws wireless earbuds"
    },
    {
        "id": "621540685",
        "url": "https://www.daraz.pk/products/i621540685.html",
        "title": "Airpods pro TwS(true wireless stereo) Airbuds with Super Sound & High Quality Touch Sensors",
        "name": "Rank Booster: Airpods Pro TWS Airbuds (621540685)",
        "keywords": "airpods pro, airbuds, wireless earbuds bluetooth, tws airbuds, bluetooth earbuds"
    },
    {
        "id": "605966087",
        "url": "https://www.daraz.pk/products/i605966087.html",
        "title": "Airpods TwS wireless Airbuds with Super Sound & High Quality Touch Sensors True Stereo Headphones",
        "name": "Rank Booster: Airpods TWS Wireless Airbuds (605966087)",
        "keywords": "airpods tws, wireless airbuds, bluetooth wireless earbuds, airpods, tws earphones"
    }
]

def setup_campaigns():
    campaign_ids = []
    with Session(engine) as session:
        for p in PRODUCTS:
            existing = session.exec(select(Campaign).where(Campaign.target_url == p["url"])).first()
            if existing:
                existing.name = p["name"]
                existing.campaign_type = "atc_rank_boost"
                existing.keyword = p["keywords"]
                existing.target_atc_count = 150
                existing.target_wishlist_count = 150
                existing.status = "running"
                existing.delay_min_sec = 8
                existing.delay_max_sec = 16
                existing.headless = True
                session.add(existing)
                session.commit()
                session.refresh(existing)
                campaign_ids.append(existing.id)
                print(f"[DB] Ready: Campaign #{existing.id} for Product {p['id']} (Current Progress: {existing.completed_atc_count}/150 ATCs)", flush=True)
            else:
                camp = Campaign(
                    name=p["name"],
                    campaign_type="atc_rank_boost",
                    target_url=p["url"],
                    keyword=p["keywords"],
                    target_orders_count=0,
                    target_atc_count=150,
                    target_wishlist_count=150,
                    completed_orders_count=0,
                    completed_atc_count=0,
                    completed_wishlist_count=0,
                    delay_min_sec=8,
                    delay_max_sec=16,
                    headless=True,
                    status="running"
                )
                session.add(camp)
                session.commit()
                session.refresh(camp)
                campaign_ids.append(camp.id)
                print(f"[DB] Created: Campaign #{camp.id} for Product {p['id']} (Target: 150 ATCs & 150 Wishlists)", flush=True)
    return campaign_ids

async def run_single_product_cycle(product_dict: dict, round_num: int):
    p = product_dict
    acc_email = f"stealth_guest_{p['id']}_{random.randint(10000, 99999)}@daraz.pk"
    
    kw_list = [k.strip() for k in p["keywords"].split(",") if k.strip()]
    selected_kw = random.choice(kw_list) if kw_list else "wireless earbuds"

    print(f"\n[Round #{round_num}] Product {p['id']}: Using keyword '{selected_kw}' | Guest Session: {acc_email}", flush=True)
    
    context, page = await browser_pool.create_account_context(
        account_email=acc_email,
        headless=True
    )

    async def log_cb(lvl, msg):
        try:
            print(f"  [{lvl.upper()}] {msg}", flush=True)
        except Exception:
            pass

    try:
        bot = DarazBotEngine(page, context, log_callback=log_cb)
        
        # 1. Organic Search and Dwell Simulation
        await bot.organic_search_and_browse(
            keyword=selected_kw,
            target_url=p["url"]
        )

        # 2. Add to Wishlist & Add to Cart
        wishlist_ok = await bot.add_to_wishlist()
        atc_ok = await bot.add_to_cart()

        # Update Progress in Database
        with Session(engine) as session:
            camp = session.exec(select(Campaign).where(Campaign.target_url == p["url"])).first()
            if camp:
                if atc_ok:
                    camp.completed_atc_count += 1
                if wishlist_ok:
                    camp.completed_wishlist_count += 1
                if camp.completed_atc_count >= camp.target_atc_count:
                    camp.status = "completed"
                session.add(camp)
                session.commit()
                print(f"  --> [DB Progress] Product {p['id']}: {camp.completed_atc_count}/{camp.target_atc_count} ATCs | {camp.completed_wishlist_count}/{camp.target_wishlist_count} Wishlists", flush=True)

        return atc_ok
    except Exception as e:
        print(f"  [ERROR] Round #{round_num} for {p['id']}: {e}", flush=True)
        return False
    finally:
        await context.close()

async def run_continuous_ranking_loop(target_total_per_product: int = 150):
    print("=" * 75, flush=True)
    print(f">>> 150 RANK BOOSTER DAEMON — 3 PRODUCTS CONTINUOUS AUTOMATION <<<", flush=True)
    print("=" * 75, flush=True)

    setup_campaigns()
    
    round_count = 1
    while True:
        # Check if all products completed
        all_done = True
        with Session(engine) as session:
            for p in PRODUCTS:
                camp = session.exec(select(Campaign).where(Campaign.target_url == p["url"])).first()
                if camp and camp.completed_atc_count < target_total_per_product:
                    all_done = False
                    break

        if all_done:
            print("\n" + "=" * 75, flush=True)
            print(f"[MISSION COMPLETE] All 3 products reached {target_total_per_product} Add-To-Carts & Wishlists successfully!", flush=True)
            print("=" * 75, flush=True)
            break

        # Rotate through all 3 products in each round
        for p in PRODUCTS:
            with Session(engine) as session:
                camp = session.exec(select(Campaign).where(Campaign.target_url == p["url"])).first()
                if camp and camp.completed_atc_count >= target_total_per_product:
                    continue # Skip already completed product

            await run_single_product_cycle(p, round_count)
            
            # Anti-ban natural human pause between products
            pause_sec = random.uniform(6.0, 12.0)
            print(f"  [Pause] Sleeping {pause_sec:.1f}s before next session...", flush=True)
            await asyncio.sleep(pause_sec)

        round_count += 1

    await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(run_continuous_ranking_loop(target_total_per_product=150))
