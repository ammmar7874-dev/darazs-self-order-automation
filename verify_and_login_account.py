import asyncio
import sys
from sqlmodel import Session, select
from backend.database import engine, Account
from backend.core.browser_pool import browser_pool
from backend.core.daraz_bot import DarazBotEngine
from backend.core.human_behavior import human_delay

async def verify_and_login(account_id_or_email: str):
    with Session(engine) as session:
        if account_id_or_email.isdigit():
            acc = session.get(Account, int(account_id_or_email))
        else:
            acc = session.exec(select(Account).where(Account.email == account_id_or_email)).first()
            
        if not acc:
            print(f"[ERROR] Account '{account_id_or_email}' not found in database.")
            return

    print("=" * 65)
    print(f"Logging in for Account: {acc.email} (Phone: {acc.phone})")
    print("Browser window will open. If OTP or Slider appears, please complete it once.")
    print("=" * 65)

    # Launch in non-headless mode so user can see/solve OTP/slider if Daraz asks
    context, page = await browser_pool.create_account_context(
        account_email=acc.email,
        headless=False
    )

    async def log_cb(lvl, msg):
        print(f"  [{lvl.upper()}] {msg}")

    bot = DarazBotEngine(page, context, log_callback=log_cb)

    try:
        success = await bot.check_and_login(
            email=acc.email,
            password=acc.password,
            phone=acc.phone
        )
        
        if success:
            print("\n[SUCCESS] Account successfully logged in and session saved permanently!")
            with Session(engine) as session:
                db_acc = session.get(Account, acc.id)
                if db_acc:
                    db_acc.status = "active"
                    session.add(db_acc)
                    session.commit()
        else:
            print("\n[NOTICE] Please finish login or OTP manually in the opened browser window if needed...")
            # Give 45 seconds for manual OTP if needed
            for i in range(45):
                await asyncio.sleep(1)
                curr = page.url.lower()
                if "user/login" not in curr and ("daraz.pk" in curr or "customer" in curr):
                    print("\n[SUCCESS] Session detected! Account saved.")
                    with Session(engine) as session:
                        db_acc = session.get(Account, acc.id)
                        if db_acc:
                            db_acc.status = "active"
                            session.add(db_acc)
                            session.commit()
                    break

        await human_delay(3.0, 5.0)
    finally:
        await context.close()
        await browser_pool.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_and_login_account.py <account_id_or_email>")
    else:
        asyncio.run(verify_and_login(sys.argv[1]))
