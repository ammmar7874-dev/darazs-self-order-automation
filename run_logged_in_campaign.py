import asyncio
import datetime
import random
import sys
from sqlmodel import Session, select
from backend.database import engine, Account, Campaign
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine
from backend.core.human_behavior import human_delay

PRODUCTS = [
    {
        "id": "667064561",
        "url": "https://www.daraz.pk/products/i667064561.html",
        "title": "Orginal TwS Airpods with Super Sound & High Quality Touch Sensor True Stereo Headphones",
        "keywords": ["wireless earbuds", "tws earbuds", "bluetooth earphones", "airpods"]
    },
    {
        "id": "621540685",
        "url": "https://www.daraz.pk/products/i621540685.html",
        "title": "Airpods pro TwS(true wireless stereo) Airbuds with Super Sound & High Quality Touch Sensors",
        "keywords": ["airpods pro", "airbuds", "wireless earbuds bluetooth", "bluetooth earbuds"]
    },
    {
        "id": "605966087",
        "url": "https://www.daraz.pk/products/i605966087.html",
        "title": "Airpods TwS wireless Airbuds with Super Sound & High Quality Touch Sensors True Stereo Headphones",
        "keywords": ["airpods tws", "wireless airbuds", "bluetooth wireless earbuds", "tws earphones"]
    }
]

async def run_logged_in_boost_for_account(acc: Account, headless: bool = False):
    print(f"\n==================================================================")
    print(f"[START] Running Real Account Boost for: {acc.email} (Phone: {acc.phone})")
    print(f"==================================================================")

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

    try:
        # Step 1: Ensure Logged In
        logged_in = await bot.check_and_login(email=acc.email, password=acc.password, phone=acc.phone)
        if not logged_in:
            print(f"  [WARNING] Account {acc.email} is not fully logged in. Attempting organic flow anyway...")

        # Step 2: Loop through each product
        for idx, prod in enumerate(PRODUCTS, 1):
            kw = random.choice(prod["keywords"])
            print(f"\n  --> [{idx}/3] Processing Product {prod['id']} with Keyword: '{kw}'")

            # 1. Organic Search & Browse with Timeout
            try:
                await asyncio.wait_for(
                    bot.organic_search_and_browse(keyword=kw, target_url=prod["url"]),
                    timeout=45.0
                )
            except Exception as ex:
                print(f"  [INFO] Dwell complete / timed out, proceeding: {ex}")
                try:
                    await page.goto(prod["url"], timeout=30000, wait_until="domcontentloaded")
                except Exception:
                    pass
            await human_delay(1.5, 3.0)

            # 2. Add to Wishlist (Verified Buyer Favorite)
            wishlist_ok = await bot.add_to_wishlist()
            await human_delay(1.0, 2.0)

            # 3. Add to Cart (Verified Buyer Cart)
            atc_ok = await bot.add_to_cart()
            await human_delay(1.5, 3.0)

            print(f"  [RESULT] Product {prod['id']}: Wishlist={'SUCCESS' if wishlist_ok else 'FAILED'} | Cart={'SUCCESS' if atc_ok else 'FAILED'}")

            # Update DB Campaign
            with Session(engine) as session:
                camp = session.exec(select(Campaign).where(Campaign.target_url == prod["url"])).first()
                if camp:
                    if atc_ok:
                        camp.completed_atc_count += 1
                    if wishlist_ok:
                        camp.completed_wishlist_count += 1
                    session.add(camp)
                    session.commit()

            # Random delay between products
            await human_delay(3.0, 6.0)

        # Mark account last used
        with Session(engine) as session:
            db_acc = session.get(Account, acc.id)
            if db_acc:
                db_acc.last_used_at = datetime.datetime.utcnow()
                session.add(db_acc)
                session.commit()

        print(f"\n[DONE] All 3 products boosted successfully with Account: {acc.email}")

    except Exception as e:
        print(f"  [ERROR] Execution failed for account {acc.email}: {e}")
    finally:
        try:
            await context.close()
        except Exception:
            pass

async def main():
    with Session(engine) as session:
        # Prioritize accounts that haven't been used yet (last_used_at is None or oldest)
        accounts = session.exec(
            select(Account)
            .where(Account.status == "active")
            .order_by(Account.last_used_at.asc().nullsfirst())
        ).all()

    if not accounts:
        print("\n[!] No active accounts found in database.")
        return

    print(f"Found {len(accounts)} active account(s) ready to boost Wishlist & ATC.")
    
    for acc in accounts:
        await run_logged_in_boost_for_account(acc, headless=False)
        await human_delay(4.0, 8.0)

    await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(main())
