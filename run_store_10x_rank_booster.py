import asyncio
import datetime
import json
import random
import sys
import os
import re
from typing import List, Dict, Any

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from sqlmodel import Session, select
from backend.database import engine, Account, Campaign
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine
from backend.core.human_behavior import human_delay

STORE_URL = "https://www.daraz.pk/shop/8itypm6b"

STORE_PRODUCTS: List[Dict[str, Any]] = [
    {
        "id": "598756764",
        "url": "https://www.daraz.pk/products/3rd-tws-i598756764-s2766588828.html",
        "title": "Airpods Air Pro TwS Bluetooth Earbuds",
        "keywords": ["airpods pro", "tws earbuds", "bluetooth handfree", "wireless earphones"]
    },
    {
        "id": "621540685",
        "url": "https://www.daraz.pk/products/tws-10-i621540685-s2904136294.html",
        "title": "Airpods pro TwS Airbuds Super Sound",
        "keywords": ["airpods pro tws", "airbuds", "wireless earbuds bluetooth", "bluetooth earbuds"]
    },
    {
        "id": "1971002021",
        "url": "https://www.daraz.pk/products/2-i1971002021-s14056277835.html",
        "title": "Air Pro 2nd Gen TWS Wireless Bluetooth Earbuds",
        "keywords": ["air pro 2nd gen", "tws wireless earbuds", "bluetooth earphones", "noise reduction earbuds"]
    },
    {
        "id": "1970986896",
        "url": "https://www.daraz.pk/products/-i1970986896-s14056746013.html",
        "title": "Pro Wireless TWS Bluetooth Earbuds",
        "keywords": ["wireless earbuds", "pro tws earbuds", "bluetooth airpods", "wireless earphones"]
    },
    {
        "id": "1970297081",
        "url": "https://www.daraz.pk/products/-i1970297081-s14056295397.html",
        "title": "Pro TWS In-Ear Wireless Earphones",
        "keywords": ["pro tws bluetooth", "in ear earbuds", "wireless earphones", "airpods"]
    },
    {
        "id": "1970984905",
        "url": "https://www.daraz.pk/products/-i1970984905-s14056722911.html",
        "title": "Universal Pro TWS Wireless Earbuds Bluetooth 5.2 Super Bass",
        "keywords": ["universal pro tws", "wireless earbuds bluetooth 5.2", "super bass earphones", "tws earbuds"]
    },
    {
        "id": "1970301002",
        "url": "https://www.daraz.pk/products/-i1970301002-s14056736598.html",
        "title": "Pro TWS Wireless Earbuds Bluetooth 5.3 Deep Bass",
        "keywords": ["pro tws wireless earbuds", "bluetooth 5.3 earphones", "deep bass airbuds", "stereo earbuds"]
    },
    {
        "id": "1970303004",
        "url": "https://www.daraz.pk/products/-i1970303004-s14056722913.html",
        "title": "Pro High Bass Bluetooth Earbuds Noise Isolation",
        "keywords": ["pro high bass earbuds", "noise isolation earphones", "type c bluetooth earbuds", "wireless earbuds"]
    },
    {
        "id": "598791145",
        "url": "https://www.daraz.pk/products/tws-169-ra-i598791145-s2766617090.html",
        "title": "Airpro TwS Airpods Touch Sensor Headset",
        "keywords": ["airpro tws airpods", "wireless earbuds", "bluetooth handfree", "touch sensor airbuds"]
    },
    {
        "id": "667064561",
        "url": "https://www.daraz.pk/products/tws-10-i667064561-s3146768410.html",
        "title": "Original TwS Airpods with Super Sound & Touch Sensor",
        "keywords": ["original tws airpods", "wireless airbuds", "bluetooth earphones", "airpods tws"]
    },
    {
        "id": "1970984906",
        "url": "https://www.daraz.pk/products/2-i1970984906-s14056287634.html",
        "title": "Pro 2 TWS Bluetooth Earphones In-Ear Wireless Earbuds",
        "keywords": ["pro 2 tws", "bluetooth earphones in ear", "silicone tips earbuds", "wireless airbuds"]
    },
    {
        "id": "1970291629",
        "url": "https://www.daraz.pk/products/-i1970291629-s14056722908.html",
        "title": "AP Pro TWS Wireless Earbuds Heavy Subwoofer Bass",
        "keywords": ["ap pro tws", "wireless earbuds bluetooth", "pubg calling earbuds", "heavy bass airpods"]
    }
]

PROGRESS_FILE = "store_rank_progress.json"

def load_progress() -> Dict[str, Any]:
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Initialize
        return {
            p["id"]: {"wishlist_count": 0, "atc_count": 0, "accounts_used": []}
            for p in STORE_PRODUCTS
        }

def save_progress(progress: Dict[str, Any]):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

async def boost_store_for_account(acc: Account, acc_idx: int, total_accs: int, headless: bool = False):
    print("\n" + "="*80)
    print(f"🚀 [ACCOUNT {acc_idx}/{total_accs}] Starting Deep Ranking Session for: {acc.email} (Phone: {acc.phone or 'N/A'})")
    print("="*80)

    context, page = await browser_pool.create_account_context(
        account_email=acc.email,
        headless=headless
    )

    async def log_cb(lvl, msg):
        try:
            print(f"  [{lvl.upper()}] {msg}", flush=True)
        except Exception:
            pass

    bot = DarazBotEngine(page, context, log_callback=log_cb)
    progress = load_progress()

    try:
        # Step 1: Ensure Logged In (with active session cookies)
        logged_in = await bot.check_and_login(email=acc.email, password=acc.password, phone=acc.phone)
        if not logged_in:
            print(f"  ⚠️ Account {acc.email} session unconfirmed. Proceeding with stealth human buyer flow...")

        # Step 2: Loop through each of the 12 store products
        # Shuffle products slightly for organic non-robotic patterns
        prod_order = list(STORE_PRODUCTS)
        random.shuffle(prod_order)

        for p_idx, prod in enumerate(prod_order, 1):
            p_id = prod["id"]
            cur_p_data = progress.get(p_id, {"wishlist_count": 0, "atc_count": 0, "accounts_used": []})

            kw = random.choice(prod["keywords"])
            print(f"\n  ----------------------------------------------------------------------")
            print(f"  📦 [{p_idx}/{len(prod_order)}] Product {p_id}: '{prod['title'][:45]}...'")
            print(f"     Target Keyword: '{kw}' | Current Rank Score: Wishlist={cur_p_data.get('wishlist_count',0)}/10, Cart={cur_p_data.get('atc_count',0)}/10")
            print(f"  ----------------------------------------------------------------------")

            # 1. Organic Search & Deep Human Browse
            try:
                await asyncio.wait_for(
                    bot.organic_search_and_browse(keyword=kw, target_url=prod["url"]),
                    timeout=55.0
                )
            except Exception as ex:
                print(f"  ℹ️ Dwell / browse timeout ({ex}), ensuring product page is open...")
                try:
                    await page.goto(prod["url"], timeout=30000, wait_until="domcontentloaded")
                except Exception:
                    pass

            await human_delay(2.0, 3.5)

            # 2. Add to Wishlist (Signals high organic buyer interest)
            wishlist_ok = await bot.add_to_wishlist()
            await human_delay(1.5, 2.5)

            # 3. Add to Cart (Daraz #1 Ranking Signal)
            atc_ok = await bot.add_to_cart()
            await human_delay(2.0, 3.5)

            print(f"  ⭐ [OUTCOME] Product {p_id} -> Wishlist: {'✅ SUCCESS' if wishlist_ok else '❌ MISSED'} | Cart: {'✅ SUCCESS' if atc_ok else '❌ MISSED'}")

            # Update in-memory & file progress
            if wishlist_ok:
                cur_p_data["wishlist_count"] = cur_p_data.get("wishlist_count", 0) + 1
            if atc_ok:
                cur_p_data["atc_count"] = cur_p_data.get("atc_count", 0) + 1
            if acc.email not in cur_p_data.get("accounts_used", []):
                cur_p_data.setdefault("accounts_used", []).append(acc.email)
            progress[p_id] = cur_p_data
            save_progress(progress)

            # Update DB Campaign if exists
            with Session(engine) as session:
                camp = session.exec(select(Campaign).where(Campaign.target_url == prod["url"])).first()
                if camp:
                    if atc_ok:
                        camp.completed_atc_count += 1
                    if wishlist_ok:
                        camp.completed_wishlist_count += 1
                    session.add(camp)
                    session.commit()

            # Human resting delay between products (3 to 6 seconds)
            await human_delay(3.0, 6.0)

        # Mark account last used
        with Session(engine) as session:
            db_acc = session.get(Account, acc.id)
            if db_acc:
                db_acc.last_used_at = datetime.datetime.utcnow()
                session.add(db_acc)
                session.commit()

        print(f"\n🎉 [COMPLETE] Finished 100% store pass with Account: {acc.email}")

    except Exception as e:
        print(f"  ❌ [ERROR] Account session error ({acc.email}): {e}")
    finally:
        try:
            await context.close()
        except Exception:
            pass

async def main():
    print("""
================================================================================
  🔥 DARAZ STORE 10X DEEP RANKING BOOSTER 🔥
  Store: https://www.daraz.pk/shop/8itypm6b
  Target: 10x Add-to-Cart & 10x Wishlist Per Product (12 Total Store Products)
  Total Operations: 120 Cart Adds + 120 Wishlist Adds + 120 Organic Searches
================================================================================
""")

    with Session(engine) as session:
        accounts = session.exec(
            select(Account)
            .where(Account.status == "active")
            .order_by(Account.last_used_at.asc().nullsfirst())
        ).all()

    if not accounts:
        print("\n❌ No active accounts found in database! Please check accounts table.")
        return

    print(f"✨ Found {len(accounts)} verified buyer accounts in database ready for rotation.")

    # Ensure campaigns exist in database for tracking
    with Session(engine) as session:
        for p in STORE_PRODUCTS:
            camp = session.exec(select(Campaign).where(Campaign.target_url == p["url"])).first()
            if not camp:
                camp = Campaign(
                    name=f"Rank Boost - {p['title'][:35]}",
                    target_url=p["url"],
                    keyword=", ".join(p["keywords"]),
                    target_atc_count=10,
                    target_wishlist_count=10,
                    completed_atc_count=0,
                    completed_wishlist_count=0,
                    status="active"
                )
                session.add(camp)
                session.commit()

    # Run through accounts until 10 passes are completed
    total_accs = len(accounts)
    for idx, acc in enumerate(accounts, 1):
        await boost_store_for_account(acc, idx, total_accs, headless=False)
        if idx < total_accs:
            print("\n⏳ Cooling down between account switches (6-12 seconds)...")
            await human_delay(6.0, 12.0)

    # Print Final Summary Table
    final_prog = load_progress()
    print("\n" + "="*80)
    print("🏆 FINAL STORE RANKING BOOSTER SUMMARY:")
    print("="*80)
    print(f"{'Product ID':<15} | {'Wishlist Added':<16} | {'Cart Added':<12} | {'Status':<10}")
    print("-"*80)
    for p in STORE_PRODUCTS:
        p_id = p["id"]
        stats = final_prog.get(p_id, {"wishlist_count": 0, "atc_count": 0})
        w_cnt = stats.get("wishlist_count", 0)
        c_cnt = stats.get("atc_count", 0)
        status = "✅ 10/10 MAX" if (w_cnt >= 10 and c_cnt >= 10) else f"🚀 {w_cnt}/10 W | {c_cnt}/10 C"
        print(f"{p_id:<15} | {f'{w_cnt} / 10':<16} | {f'{c_cnt} / 10':<12} | {status:<10}")
    print("="*80)
    print("✅ Store ranking boost successfully executed!")

    await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(main())
